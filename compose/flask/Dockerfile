FROM python:3.6

ENV PYTHONUNBUFFERED 1

COPY . /app

RUN pip3 install  -r /app/requirements.txt

RUN chmod +x /app/compose/flask/gunicorn.sh
CMD /app/compose/flask/gunicorn.sh
