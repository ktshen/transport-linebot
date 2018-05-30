FROM python:3.6

ENV PYTHONUNBUFFERED 1

COPY . /app

RUN pip3 install  -r /app/requirements.txt

ENTRYPOINT ["python", "/app/routine_update.py"]
