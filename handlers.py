import re
from datetime import datetime, timedelta
from flask import current_app
from linebot.models import (
    MessageEvent, JoinEvent, LeaveEvent, FollowEvent, UnfollowEvent,
    PostbackEvent, TextSendMessage, TemplateSendMessage, ButtonsTemplate,
    MessageTemplateAction, DatetimePickerTemplateAction
)
from linebot.exceptions import LineBotApiError
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from models import TRA_QuestionState, TRA_TableEntry, TRA_TrainTimeTable
from data import TRA_STATION_CODE2NAME
from utils import pre_process_text


def create_error_text_message(text=""):
    if not text:
        text = "系統發生錯誤，請稍後再試，謝謝～"
    return TextSendMessage(text=text)


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


def search_TRA_train(event):
    old_states = current_app.session.query(TRA_QuestionState).filter_by(expired=False) \
                                    .filter_by(user=event.source.user_id).all()
    for s in old_states:
        s.expired = True
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
    q_1 = current_app.session.query(TRA_TrainTimeTable).join("entries") \
                             .filter(TRA_TableEntry.station_name == qs.departure_station) \
                             .filter(TRA_TableEntry.departure_time > qs.departure_time)
    q_2 = current_app.session.query(TRA_TrainTimeTable).join("entries") \
                             .filter(TRA_TableEntry.station_name == qs.destination_station) \
                             .filter(TRA_TableEntry.arrival_time > qs.departure_time)
    q = q_1.intersect(q_2)
    suitable_trains = list()
    for t in q:
        dep_q = current_app.session.query(TRA_TableEntry) \
                                   .filter(TRA_TableEntry.timetable == t) \
                                   .filter_by(station_name=qs.departure_station) \
                                   .filter(TRA_TableEntry.departure_time > qs.departure_time) \
                                   .order_by(TRA_TableEntry.departure_time)
        try:
            dep_entry = dep_q.one()
        except MultipleResultsFound:
            dep_entry = dep_q.first()
        dest_q = current_app.session.query(TRA_TableEntry) \
                                    .filter(TRA_TableEntry.timetable == t) \
                                    .filter_by(station_name=qs.destination_station) \
                                    .filter(dep_entry.departure_time < TRA_TableEntry.arrival_time) \
                                    .order_by(TRA_TableEntry.departure_time)
        try:
            dest_entry = dest_q.one()
        except MultipleResultsFound:
            dest_entry = dest_q.first()
        except NoResultFound:
            continue
        suitable_trains.append([t, dep_entry, dest_entry])
    suitable_trains = sorted(suitable_trains, key=lambda x: x[1].departure_time)
    if not suitable_trains:
        text = "無適合班次"
    else:
        text = "適合班次如下  {0} → {1} \n" \
               "車次   車種  開車時間  抵達時間\n".format(qs.departure_station, qs.destination_station)
        fmt = "{0:0>4}  {1:^2}     {2}        {3}\n"
        for _l in suitable_trains:
            text = text + fmt.format(_l[0].train.train_no, _l[0].train.train_type,
                                     _l[1].departure_time.strftime("%H:%M"),
                                     _l[2].arrival_time.strftime("%H:%M"))
    q.expired = True
    return TextSendMessage(text=text)


def ask_TRA_question_states(event):
    now = datetime.now()
    q = current_app.session.query(TRA_QuestionState).filter_by(expired=False) \
                           .filter_by(user=event.source.user_id) \
                           .filter(TRA_QuestionState.update > (now - timedelta(hours=1)))
    if hasattr(event.source, "group_id"):
        q = q.filter_by(group=event.source.group_id)
    try:
        q = q.one()
    except NoResultFound:
        return None

    message = None
    if not q.departure_station:
        res = match_TRA_station_name(event.message.text)
        if res:
            q.departure_station = res
            message = TextSendMessage(text="請輸入目的站")
    elif not q.destination_station:
        res = match_TRA_station_name(event.message.text)
        if res and res != q.departure_station:
            q.destination_station = res
            title = '請選擇搭乘時間: {0} → {1}'.format(q.departure_station, q.destination_station)
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
        elif res == q.departure_station:
            message = create_error_text_message(
                text="輸入的目的站與起程站皆是{0}，請重新輸入有效目的站".format(res))
    elif not q.departure_time and isinstance(event, PostbackEvent):
        dt = event.postback.params["datetime"]
        dt = datetime.strptime(dt, "%Y-%m-%dT%H:%M")
        q.departure_time = dt
        message = request_TRA_matching_train(q)
    if message:
        q.update = now
        current_app.session.commit()
    return message


def match_text_and_assign(event):
    """
    Assigned function should return a Message Object
    """
    res = None
    text = event.message.text
    if re.fullmatch(r'[ ]*([tT]+|查(交通|時刻表|班次)?)', text):
        res = request_main_menu()
    elif re.fullmatch(r'[ ]*查?(台鐵|TRA)', text):
        res = search_TRA_train(event)
    else:
        res = ask_TRA_question_states(event)
    return res


def handle_message_event(event):
    try:
        response = match_text_and_assign(event)
    except LineBotApiError as e:
        current_app.logger.error(e.error.message)
        current_app.logger.error(e.error.details)
        response = create_error_text_message()
    if response is not None:
        current_app.linebot.reply_message(event.reply_token, response)


def handle_follow_event(ev):
    pass


def handle_unfollow_event(ev):
    pass


def handle_postback_event(event):
    response = ask_TRA_question_states(event)

    if response is not None:
        current_app.linebot.reply_message(event.reply_token, response)


def handle_events(events):
    for ev in events:
        if isinstance(ev, MessageEvent):
            handle_message_event(ev)
        elif isinstance(ev, FollowEvent) or isinstance(ev, JoinEvent):
            handle_follow_event(ev)
        elif isinstance(ev, UnfollowEvent) or isinstance(ev, LeaveEvent):
            handle_unfollow_event(ev)
        elif isinstance(ev, PostbackEvent):
            handle_postback_event(ev)
        else:
            pass
