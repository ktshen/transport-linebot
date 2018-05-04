import re
from datetime import datetime, timedelta
from flask import current_app
from linebot.models import (
    MessageEvent, JoinEvent, LeaveEvent, FollowEvent, UnfollowEvent,
    PostbackEvent, TextSendMessage, TemplateSendMessage, ButtonsTemplate,
    MessageTemplateAction, DatetimePickerTemplateAction
)
from linebot.exceptions import LineBotApiError
from sqlalchemy.orm.exc import NoResultFound

from models import TRA_QuestionState
from data import TRA_STATION_CODE2NAME
from utils import pre_process_text


def response_error_message(text=""):
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
    current_app.session.add()
    current_app.commit()
    message = TextSendMessage(text="請輸入啟程站")
    return message


def match_TRA_station_name(text):
    stations_name = TRA_STATION_CODE2NAME.values()
    text = pre_process_text(text)
    for s in stations_name:
        if re.match(s, text):
            return s
    return None


def request_TRA_matching_train(question_state):
    pass


def ask_TRA_question_states(event):
    now = datetime.now()
    q = current_app.session.query(TRA_QuestionState).filter_by(expired=False) \
                           .filter_by(user=event.source.user_id) \
                           .filter(TRA_QuestionState.update < (now - timedelta(hours=1)))
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
        if res:
            q.destination_station = res
            title = '請選擇搭乘時間: {0} -> {1}'.format(q.departure_station, q.destination_station)
            message = TemplateSendMessage(
                alt_text='請選擇搭乘時間',
                template=ButtonsTemplate(
                    title=title,
                    text='點擊選擇',
                    actions=[
                        DatetimePickerTemplateAction(label='選擇時間', data='datetime_postback',
                                                     mode='datetime'),
                    ]
                )
            )
    elif q.departure_time and isinstance(event, PostbackEvent):
        dt = q.postback.params["datetime"]
        dt = datetime.strptime(dt, "%Y-%m-%dT%H:%M")
        q.departure_time = dt
        # message = request_TRA_matching_train(q)
        message = TextSendMessage(text="完成～～")
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
    if re.fullmatch(r'[ ]*([tT]|查(交通)?)', text):
        res = request_main_menu()
    elif re.fullmatch(r'[ ]*查?(台鐵|TRA)', text):
        res = search_TRA_train(event)
    else:
        res = ask_TRA_question_states(event)
        if res:
            return res
    return res


def handle_message_event(event):
    try:
        response = match_text_and_assign(event)
    except LineBotApiError as e:
        current_app.logger.error(e)
        response = response_error_message()
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
