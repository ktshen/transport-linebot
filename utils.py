import os
import sys
from hashlib import sha1
import hmac
from wsgiref.handlers import format_date_time
from datetime import datetime, date
from time import mktime
import base64
import requests
import re

def request_MOTC(url):
    """
    To request data from http://ptx.transportdata.tw/MOTC#!/, a signature is needed, and the generation
    method of which is specified at its website.
    (https://gist.github.com/ptxmotc/383118204ecf7192bdf96bc0197bb981#api)
    """
    app_id = os.getenv('PTX_APP_ID', None)
    app_key = os.getenv('PTX_APP_KEY', None)
    if app_id is None or app_key is None:
        print("Please specify PTX_APP_ID and PTX_APP_KEY properly as environmental variable.")
        sys.exit(1)
    xdate = format_date_time(mktime(datetime.now().timetuple()))
    hashed = hmac.new(bytearray(app_key, 'utf-8'), ('x-date: ' + xdate).encode('utf-8'), sha1)
    signature = base64.b64encode(hashed.digest()).decode()
    authorization = 'hmac username="{0}", algorithm="hmac-sha1", headers="x-date", signature="{1}"'\
                    .format(app_id, signature)
    headers = {
        "Authorization": authorization,
        "x-date": xdate,
        "Accept-Encoding": "gzip, deflate",
    }
    return requests.get(url, headers=headers)


def convert_date_to_string(date_input):
    """
    Convert date to YYYY-MM-DD
    """
    if isinstance(date_input, date):
        return date_input.strftime("%Y-%m-%d")
    else:
        raise TypeError("Input {0} is not a date object".format(type(date_input)))


def pre_process_text(text):
    """
    Deal with word like "臺" and "台", replace it with appropriate word
    """
    text = re.sub(r'台', '臺', text)
    return text