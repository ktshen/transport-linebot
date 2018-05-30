from flask import request, abort
from flask import current_app
from flask.views import View
from linebot.exceptions import InvalidSignatureError
from datetime import datetime

from handlers import handle_events


def register_url(app):
    """
    Add new routing rules here
    """
    app.add_url_rule('/', view_func=IndexView.as_view("index"))
    app.add_url_rule('/callback', view_func=LineRequestView.as_view('line'))


class IndexView(View):
    def dispatch_request(self):
        return "Hello From Triple T at {0}.".format(datetime.now().strftime("%Y/%m/%d %H:%M"))


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
            events = current_app.parser.parse(body, signature)
        except InvalidSignatureError:
            current_app.logger.error("Invalid Signature.")
            abort(400)
        handle_events(events)
        return 'OK'
