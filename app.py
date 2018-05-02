from flask import Flask
from views import register_url
from linebot import LineBotApi, WebhookParser
from dotenv import load_dotenv
import os
import sys


app = Flask(__name__)

# Load env variables
dotenv_path = os.path.join(os.getcwd(), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

# Set up config
app.config.update({
    "DEBUG": True if os.getenv("DEBUG") == "True" else False,
    "DATABASE_URI": os.getenv("DATABASE_URI"),
    "CHANNEL_ACCESS_TOKEN": os.getenv("CHANNEL_ACCESS_TOKEN", None),
    "CHANNEL_SECRET":  os.getenv("CHANNEL_SECRET", None),
})

# Create Linebot instance
try:
    app.linebot = LineBotApi(app.config['CHANNEL_ACCESS_TOKEN'])
    app.parser = WebhookParser(app.config['CHANNEL_SECRET'])
except KeyError:
    app.logger.error("Please specify line CHANNEL_ACCESS_TOKEN and CHANNEL_SECRET.")
    sys.exit(1)

# Register routing rule
register_url(app)


if __name__ == "__main__":
    app.run()

