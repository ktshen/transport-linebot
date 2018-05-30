#!/bin/sh
/usr/local/bin/gunicorn -w 2 -b 0.0.0.0:5000 --chdir=/app --worker-class=gevent wsgi:application