import os
from hashlib import sha1
import hmac
from wsgiref.handlers import format_date_time
from datetime import datetime, date
from time import mktime
import base64
import requests
import re
import time


keys_candidates = list()
with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "ptx_keys.txt"), "r") as infile:
    ID = KEY = ""
    for line in infile:
        line = line.rstrip('\n')
        if line and not ID:
            ID = line
        elif line and not KEY:
            KEY = line
            keys_candidates.append((ID, KEY))
            ID = KEY = ""


def request_MOTC(url):
    """
    To request data from http://ptx.transportdata.tw/MOTC#!/, a signature is needed, and the generation
    method of which is specified at its website.
    (https://gist.github.com/ptxmotc/383118204ecf7192bdf96bc0197bb981#api)
    """
    def prepare_headers(app_id, app_key):
        xdate = format_date_time(mktime(datetime.now().timetuple()))
        hashed = hmac.new(bytearray(app_key, 'utf-8'), ('x-date: ' + xdate).encode('utf-8'), sha1)
        signature = base64.b64encode(hashed.digest()).decode()
        authorization = 'hmac username="{0}", algorithm="hmac-sha1", headers="x-date", signature="{1}"'\
                        .format(app_id, signature)
        return {
            "Authorization": authorization,
            "x-date": xdate,
            "Accept-Encoding": "gzip, deflate",
        }

    url += "?$format=JSON"
    r = None
    # In my experience, PTX platform is not stable, so try multiple times to work around
    # If message in response, then the problem is probably related to the key, so change the key
    # If message is an empty list, then try again with that key
    for i in range(len(keys_candidates)):
        headers = prepare_headers(keys_candidates[i][0], keys_candidates[i][1])
        for j in range(5):
            r = requests.get(url, headers=headers)
            r = r.json()
            if "message" in r:
                break
            elif not r:
                time.sleep(1)
                continue
            else:
                return r
    return r


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
