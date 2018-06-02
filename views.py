import os
from flask import request, abort
from flask import current_app
from flask.views import View
from linebot.exceptions import InvalidSignatureError
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from handlers import handle_events

engine = create_engine(os.environ["DATABASE_URI"])
Session = sessionmaker(bind=engine)


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
        # Create new session for each request and tear it down after the process ends
        # For more information look at the link below:
        # http://docs.sqlalchemy.org/en/latest/orm/session_basics.html#when-do-i-construct-a-session-when-do-i-commit-it-and-when-do-i-close-it
        current_app.session = Session()
        handle_events(events)
        current_app.session.commit()
        current_app.session.close()
        return 'OK'
