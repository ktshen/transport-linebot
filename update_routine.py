import os
from models import Base
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from build_database import build_TRA_Database_by_date
from utils import convert_date_to_string
import time

RUN_JOBS_AT_TIME = "00:00"

try:
    DATABASE_URI = os.environ["DATABASE_URI"]
except KeyError:
    raise KeyError("Please specify DATABASE_URI in environment")

engine = create_engine(DATABASE_URI)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


def build_TRA():
    """
    Building strategy for TRA:
    1. update tomorrow's data on every midnight anyway
    2. make sure that data within two weeks has existed
    """
    today = datetime.now().date()
    for i in range(14):
        d = today + timedelta(i)
        ignore_built = True if i == 0 else False
        resp = build_TRA_Database_by_date(d, session, ignore_built)
        print("Update TRA DATABASE on {0}, result={1}".format(convert_date_to_string(d),
                                                              resp.message))


def main():
    # Specify periodic jobs here
    JOB_QUEUE = [build_TRA]
    invoked_time = datetime.strptime(RUN_JOBS_AT_TIME, "%H:%M").time()
    while True:
        time.sleep(60)
        if datetime.now().time() == invoked_time:
            for job in JOB_QUEUE:
                try:
                    job()
                except Exception as e:
                    print(e)
                    pass


if __name__ == "__main__":
    main()
