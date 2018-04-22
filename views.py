from flask import request, abort
from flask import current_app
from flask.views import View
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)


def register_url(app):
    app.add_url_rule('/', view_func=IndexView.as_view("index"))
    app.add_url_rule('/callback', view_func=LineRequestView.as_view('line'))


class IndexView(View):
    def dispatch_request(self):
        return "Hello From Triple T."


class LineRequestView(View):
    methods = ["POST"]

    def dispatch_request(self):
        # get X-Line-Signature header value
        signature = request.headers['X-Line-Signature']

        # get request body as text
        body = request.get_data(as_text=True)
        current_app.logger.info("Request body: " + body)
        # handle webhook body
        try:
            current_app.handler.handle(body, signature)
        except InvalidSignatureError:
            abort(400)
        return 'OK'


@current_app.handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    current_app.linebot.reply_message(
        event.reply_token,
        TextSendMessage(text="Hello Bruce."))




