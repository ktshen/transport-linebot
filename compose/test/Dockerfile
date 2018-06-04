FROM python:3.6

ENV PYTHONUNBUFFERED 1

ADD requirements.txt /app/
RUN pip3 install  -r /app/requirements.txt

COPY . /app

RUN pip3 install  -r /app/requirements.txt

WORKDIR "/app"

ENTRYPOINT ["python", "-m", "unittest"]
