FROM python:3.6

ENV PYTHONUNBUFFERED 1

ADD requirements.txt /app/
RUN pip3 install  -r /app/requirements.txt

COPY . /app

RUN chmod +x /app/compose/flask/gunicorn.sh
CMD /app/compose/flask/gunicorn.sh
