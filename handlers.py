import re
import os
from datetime import datetime, timedelta, time
from flask import current_app
from linebot.models import (
    MessageEvent, JoinEvent, LeaveEvent, FollowEvent, UnfollowEvent,
    PostbackEvent, TextSendMessage, TemplateSendMessage, ButtonsTemplate,
    MessageTemplateAction, DatetimePickerTemplateAction
)
from linebot.exceptions import LineBotApiError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import and_
from models import (
    User, Group, TRA_QuestionState, TRA_TableEntry, TRA_TrainTimeTable,
    THSR_QuestionState, THSR_TableEntry, THSR_TrainTimeTable
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from data import TRA_STATION_CODE2NAME, THSR_STATION_CODE2NAME
from utils import pre_process_text

INTRO_TEXT = "hi~ 我是火車時刻機器人🚆\n" \
             "> 輸入: 大寫或小寫T \n" \
             "就可以呼叫我喔～～😘\n\n" \
             "其他指令\n" \
             "- issue (回報問題)\n" \
             "- github (歡迎共同開發)\n" \
             "註：若沒有反應請稍待或重新輸入\n" \
             "因主機較舊且網路不好，感謝～"

engine = create_engine(os.environ["DATABASE_URI"])
Session = sessionmaker(bind=engine)


def create_error_text_message(text=""):
    if not text:
        text = "系統發生錯誤，請稍後再試，謝謝～"
    return TextSendMessage(text=text)


def request_matching_train(qs, train_type):
    """
    Since the algorithm is same for both TRA and THSR,
    I believe this function can be an independent function
    """
    if train_type == "TRA":
        timetableclass = TRA_TrainTimeTable
        table_entry_class = TRA_TableEntry
    elif train_type == "THSR":
        timetableclass = THSR_TrainTimeTable
        table_entry_class = THSR_TableEntry
    if time(0) < qs.departure_time.time() < time(3):
        request_date = qs.departure_time.date() - timedelta(1)
    else:
        request_date = qs.departure_time.date()
    q = current_app.session.query(timetableclass).filter(timetableclass.date == request_date) \
        .filter(
        and_(timetableclass.entries.any(and_(
            table_entry_class.station_name == qs.departure_station,
            table_entry_class.departure_time > qs.departure_time,
            table_entry_class.departure_time < qs.departure_time + timedelta(hours=5)
        )),
            timetableclass.entries.any(and_(table_entry_class.station_name == qs.destination_station,
                                            table_entry_class.arrival_time > qs.departure_time))
        )
    )
    suitable_trains = list()
    for t in q:
        dep_q = current_app.session.query(table_entry_class) \
            .filter(table_entry_class.timetable == t) \
            .filter_by(station_name=qs.departure_station) \
            .filter(and_(table_entry_class.departure_time > qs.departure_time,
                         table_entry_class.departure_time < qs.departure_time + timedelta(hours=5))) \
            .order_by(table_entry_class.departure_time)
        try:
            dep_entry = dep_q.one()
        except MultipleResultsFound:
            dep_entry = dep_q.first()
        dest_q = current_app.session.query(table_entry_class) \
            .filter(table_entry_class.timetable == t) \
            .filter_by(station_name=qs.destination_station) \
            .filter(dep_entry.departure_time < table_entry_class.arrival_time) \
            .order_by(table_entry_class.departure_time)
        try:
            dest_entry = dest_q.one()
        except MultipleResultsFound:
            dest_entry = dest_q.first()
        except NoResultFound:
            continue
        suitable_trains.append([t, dep_entry, dest_entry])
    suitable_trains = sorted(suitable_trains, key=lambda x: x[1].departure_time)
    return suitable_trains


def expire_user_all_questionstates(user_id):
    old_states = current_app.session.query(TRA_QuestionState).filter_by(expired=False) \
        .filter_by(user=user_id).all()
    for s in old_states:
        s.expired = True
    old_states = current_app.session.query(THSR_QuestionState).filter_by(expired=False) \
        .filter_by(user=user_id).all()
    for s in old_states:
        s.expired = True


def request_main_menu():
    menu = TemplateSendMessage(
        alt_text='請選擇查詢交通類型',  # Alert message
        template=ButtonsTemplate(
            title='查詢交通類型',
            text='點擊選擇',
            actions=[
                MessageTemplateAction(
                    label='台鐵',
                    text='查台鐵'
                ),
                MessageTemplateAction(
                    label='高鐵',
                    text='查高鐵'
                ),
            ]
        )
    )
    return menu


def request_github():
    return TextSendMessage(text="https://github.com/ktshen/transport-linebot")


def request_issue():
    return TextSendMessage(text="請寄信到 ktshen.meow@gmail.com 說明問題\n"
                                "或者到github發issue喔：\n"
                                "https://github.com/ktshen/transport-linebot\n"
                                "thank you 👍")


def search_TRA_train(event):
    expire_user_all_questionstates(event.source.user_id)
    q_state = TRA_QuestionState(group=None if not hasattr(event.source, "group_id") else event.source.group_id,
                                user=event.source.user_id)
    current_app.session.add(q_state)
    current_app.session.commit()
    message = TextSendMessage(text="請輸入起程站")
    return message


def match_TRA_station_name(text):
    stations_name = TRA_STATION_CODE2NAME.values()
    text = pre_process_text(text)
    for s in stations_name:
        if re.match(s, text):
            return s
    return None


def request_TRA_matching_train(qs):
    return request_matching_train(qs, "TRA")


def search_THSR_train(event):
    expire_user_all_questionstates(event.source.user_id)
    q_state = THSR_QuestionState(group=None if not hasattr(event.source, "group_id") else event.source.group_id,
                                 user=event.source.user_id)
    current_app.session.add(q_state)
    current_app.session.commit()
    message = TextSendMessage(text="請輸入起程站")
    return message


def match_THSR_station_name(text):
    stations_name = THSR_STATION_CODE2NAME.values()
    text = pre_process_text(text)
    for s in stations_name:
        if re.match(s, text):
            return s
    return None


def request_THSR_matching_train(qs):
    return request_matching_train(qs, "THSR")


def ask_question_states(event):
    now = datetime.now()
    train_type = ""
    qs = current_app.session.query(TRA_QuestionState).filter_by(expired=False) \
        .filter_by(user=event.source.user_id) \
        .filter(TRA_QuestionState.update > (now - timedelta(hours=1)))
    if hasattr(event.source, "group_id"):
        qs = qs.filter_by(group=event.source.group_id)
    try:
        qs = qs.one()
        train_type = "TRA"
    except NoResultFound:
        pass
    except MultipleResultsFound:
        for i in qs.all():
            i.expired = True

    if not train_type:
        qs = current_app.session.query(THSR_QuestionState).filter_by(expired=False) \
            .filter_by(user=event.source.user_id) \
            .filter(THSR_QuestionState.update > (now - timedelta(hours=1)))
        try:
            qs = qs.one()
            train_type = "THSR"
        except NoResultFound:
            return None
        except MultipleResultsFound:
            for i in qs.all():
                i.expired = True
            return None

    message = None
    if not qs.departure_station:
        if train_type == "TRA":
            res = match_TRA_station_name(event.message.text)
        else:
            res = match_THSR_station_name(event.message.text)
        if res:
            qs.departure_station = res
            message = TextSendMessage(text="請輸入目的站")
    elif not qs.destination_station:
        if train_type == "TRA":
            res = match_TRA_station_name(event.message.text)
        else:
            res = match_THSR_station_name(event.message.text)
        if res and res != qs.departure_station:
            qs.destination_station = res
            title = '請選擇搭乘時間: {0} → {1}'.format(qs.departure_station, qs.destination_station)
            message = TemplateSendMessage(
                alt_text='請選擇搭乘時間',
                template=ButtonsTemplate(
                    title=title,
                    text='點擊選擇',
                    actions=[
                        DatetimePickerTemplateAction(label='搭乘時間', data='datetime_postback',
                                                     mode='datetime'),
                    ]
                )
            )
        elif res == qs.departure_station:
            message = create_error_text_message(
                text="輸入的目的站與起程站皆是{0}，請重新輸入有效目的站".format(res))
    elif isinstance(event, PostbackEvent) and qs.departure_station and qs.destination_station:
        try:
            dt = event.postback.params["datetime"]
            dt = datetime.strptime(dt, "%Y-%m-%dT%H:%M")
            qs.departure_time = dt
            if train_type == "TRA":
                suitable_trains = request_TRA_matching_train(qs)
            else:
                suitable_trains = request_THSR_matching_train(qs)
            actions = [DatetimePickerTemplateAction(label='更換搭乘時間', data='datetime_postback', mode='datetime'),
                       MessageTemplateAction(label='新的搜尋', text='T')]
            if not suitable_trains:
                text = "無適合班次"
            elif train_type == "TRA":
                text = "車次   車種      開車         抵達\n"
                fmt = "{0:0>4}  {1:^2}     {2}       {3}\n"
                count = 0
                for _l in suitable_trains:
                    text = text + fmt.format(_l[0].train.train_no, _l[0].train.train_type,
                                             _l[1].departure_time.strftime("%H:%M"),
                                             _l[2].arrival_time.strftime("%H:%M"))
                    count += 1
                    # Total word number of a post is limited
                    if len(text) > 125:
                        break
                if len(suitable_trains) > count:
                    actions.insert(0, MessageTemplateAction(label='列出更多', text='列出更多'))
            else:
                text = "車次     開車時間    抵達時間\n".format(qs.departure_station, qs.destination_station)
                fmt = "{0:0>4}       {1}          {2}\n"
                count = 0
                for _l in suitable_trains:
                    text = text + fmt.format(_l[0].train.train_no,
                                             _l[1].departure_time.strftime("%H:%M"),
                                             _l[2].arrival_time.strftime("%H:%M"))
                    count += 1
                    if len(text) > 125:
                        break
                if len(suitable_trains) > count:
                    actions.insert(0, MessageTemplateAction(label='列出更多', text='列出更多'))
            message = TemplateSendMessage(
                alt_text='搜尋結果: {0} → {1}'.format(qs.departure_station, qs.destination_station),
                template=ButtonsTemplate(text=text, actions=actions)
            )
        except KeyError:
            pass
    elif event.message.text == "列出更多" and qs.departure_station and qs.destination_station and qs.departure_time:
        if train_type == "TRA":
            suitable_trains = request_TRA_matching_train(qs)
        else:
            suitable_trains = request_THSR_matching_train(qs)
        if not suitable_trains:
            text = "無適合班次"
        elif train_type == "TRA":
            text = "適合班次如下  {0} → {1} \n" \
                   "車次   車種  開車時間  抵達時間\n".format(qs.departure_station, qs.destination_station)
            fmt = "{0:0>4}  {1:^2}     {2}        {3}\n"
            for _l in suitable_trains:
                text = text + fmt.format(_l[0].train.train_no, _l[0].train.train_type,
                                         _l[1].departure_time.strftime("%H:%M"),
                                         _l[2].arrival_time.strftime("%H:%M"))
                if len(text) > 1000:
                    text = text + "More..."
                    break
        else:
            text = "適合班次如下  {0} → {1} \n" \
                   "車次     開車時間    抵達時間\n".format(qs.departure_station, qs.destination_station)
            fmt = "{0:0>4}       {1}          {2}\n"
            for _l in suitable_trains:
                text = text + fmt.format(_l[0].train.train_no,
                                         _l[1].departure_time.strftime("%H:%M"),
                                         _l[2].arrival_time.strftime("%H:%M"))
                if len(text) > 1000:
                    text = text + "More..."
                    break
        message = TextSendMessage(text=text)
    if message:
        qs.update = now
    return message


def match_text_and_assign(event):
    """
    Assigned function should return a Message Object
    """
    text = event.message.text
    if re.fullmatch(r'^[ ]*([tT]+|查(交通|時刻表|班次)?)$', text):
        res = request_main_menu()
    elif re.fullmatch(r'^[ ]*查?([臺台]鐵|TRA)$', text):
        res = search_TRA_train(event)
    elif re.fullmatch(r'^[ ]*查?(高鐵|THSR)$', text):
        res = search_THSR_train(event)
    elif re.fullmatch(r'^[Gg]ithub$', text):
        res = request_github()
    elif re.fullmatch(r'^issue$', text):
        res = request_issue()
    else:
        res = ask_question_states(event)
    return res


def handle_message_event(event):
    try:
        response = match_text_and_assign(event)
    except LineBotApiError as e:
        current_app.logger.error(e.error.message)
        current_app.logger.error(e.error.details)
        response = create_error_text_message()
    return response


def unfollow_user(user_id):
    q = current_app.session.query(User).filter_by(user_id=user_id) \
        .filter_by(following=True).all()
    for i in q:
        i.following = False
        i.unfollow_datetime = datetime.now()


def handle_follow_event(event):
    text = INTRO_TEXT
    unfollow_user(user_id=event.source.user_id)
    new_user = User(event.source.user_id)
    current_app.session.add(new_user)
    current_app.session.commit()
    return TextSendMessage(text=text)


def handle_unfollow_event(event):
    unfollow_user(user_id=event.source.user_id)


def leave_group(group_id):
    q = current_app.session.query(Group).filter_by(group_id=group_id) \
        .filter_by(joinning=True).all()
    for i in q:
        i.joinning = False
        i.leave_datetime = datetime.now()


def handle_join_event(event):
    text = INTRO_TEXT
    leave_group(event.source.group_id)
    new_group = Group(event.source.group_id)
    current_app.session.add(new_group)
    current_app.session.commit()
    return TextSendMessage(text=text)


def handle_leave_event(event):
    leave_group(event.source.group_id)


def handle_postback_event(event):
    return ask_question_states(event)


def handle_events(events):
    for ev in events:
        # Create new session for each request and tear it down after the process ends
        # For more information look at the link below:
        # http://docs.sqlalchemy.org/en/latest/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it
        current_app.session = Session()
        response = None
        if isinstance(ev, MessageEvent):
            response = handle_message_event(ev)
        elif isinstance(ev, FollowEvent):
            response = handle_follow_event(ev)
        elif isinstance(ev, UnfollowEvent):
            handle_unfollow_event(ev)
        elif isinstance(ev, JoinEvent):
            response = handle_join_event(ev)
        elif isinstance(ev, LeaveEvent):
            handle_leave_event(ev)
        elif isinstance(ev, PostbackEvent):
            response = handle_postback_event(ev)
        else:
            pass
        current_app.session.commit()
        current_app.session.close()
        if response is not None:
            current_app.linebot.reply_message(ev.reply_token, response)
