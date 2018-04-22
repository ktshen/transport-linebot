from flask import Flask
from .views import register_url
from linebot import LineBotApi, WebhookHandler

app = Flask(__name__)
app.config.from_pyfile("settings.py")
app.linebot = LineBotApi(app.config['CHANNEL_ACCESS_TOKEN'])
app.handler = WebhookHandler(app.config['CHANNEL_SECRET'])
register_url(app)


if __name__ == "__main__":
    app.run()

