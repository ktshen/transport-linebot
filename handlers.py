from flask import current_app
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FollowEvent, UnfollowEvent,
    PostbackEvent, JoinEvent, LeaveEvent,
)


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


def handle_message_event(event):
    try:
        current_app.linebot.reply_message(
            event.reply_token,
            TextSendMessage(text="Hello Bruce."))
    except current_app.linebot.exceptions.LineBotApiError as e:
        current_app.logger.error(e)


def handle_follow_event(ev):
    pass


def handle_unfollow_event(ev):
    pass


def handle_postback_event(ev):
    pass

