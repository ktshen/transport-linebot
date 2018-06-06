import os
import time
from utils import convert_date_to_string
from dotenv import load_dotenv
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from build_database import (
    build_TRA_database_by_date, remove_TRA_timetable_by_date,
    build_THSR_database_by_date, remove_THSR_timetable_by_date
)
from models import (
    Base, TRA_BuildingStatusOnDate, THSR_BuildingStatusOnDate
)

# Load env variables
dotenv_path = os.path.join(os.getcwd(), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

try:
    DATABASE_URI = os.environ["DATABASE_URI"]
except KeyError:
    raise KeyError("Please specify DATABASE_URI in environment")

time.sleep(5) # wait for postgresql to start
engine = create_engine(DATABASE_URI)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)


def build_TRA():
    """
    台鐵提供近60天每日時刻表
    Building strategy for TRA:
    1. update tomorrow's data on every midnight anyway
    2. make sure that data within a month has existed
    """
    session = Session()
    today = datetime.now().date()
    for i in range(60):
        d = today + timedelta(i)
        print("Start building TRA DATABASE on {0}".format(convert_date_to_string(d)))
        resp = build_TRA_database_by_date(d, session)
        print("Finish TRA DATABASE on {0}, result={1}".format(convert_date_to_string(d),
                                                              resp.message))
    session.close()


def clear_TRA_history():
    session = Session()
    history_date = (datetime.now() - timedelta(1)).date()
    q = session.query(TRA_BuildingStatusOnDate) \
               .filter(TRA_BuildingStatusOnDate.assigned_date < history_date).all()
    if not q:
        return True
    for s in q:
        remove_TRA_timetable_by_date(s.assigned_date, session)
    session.close()


def build_THSR():
    """
    高鐵提供近45天每日時刻表
    """
    session = Session()
    today = datetime.now().date()
    for i in range(45):
        d = today + timedelta(i)
        print("Start building THSR DATABASE on {0}".format(convert_date_to_string(d)))
        resp = build_THSR_database_by_date(d, session)
        print("Finish THSR DATABASE on {0}, result={1}".format(convert_date_to_string(d),
                                                               resp.message))
    session.close()


def clear_THSR_history():
    session = Session()
    history_date = (datetime.now() - timedelta(1)).date()
    q = session.query(THSR_BuildingStatusOnDate) \
               .filter(THSR_BuildingStatusOnDate.assigned_date < history_date).all()
    if not q:
        return True
    for s in q:
        remove_THSR_timetable_by_date(s.assigned_date, session)
    session.close()


# 24-HOUR
RUN_JOBS_AT_TIME = "00:00"
# Specify periodic jobs here
JOB_QUEUE = [build_TRA, clear_TRA_history, build_THSR, clear_THSR_history]


def run_all_job():
    for job in JOB_QUEUE:
        try:
            job()
        except Exception as e:
            print(e)
            pass


def main():
    run_all_job()
    invoked_time = datetime.strptime(RUN_JOBS_AT_TIME, "%H:%M").time()
    while True:
        time.sleep(60)
        now = datetime.now()
        if now.time() == invoked_time:
            print("Start Running Jobs at {0}".format(now.strftime("%Y-%m-%d %H:%M")))
            run_all_job()


if __name__ == "__main__":
    try:
        print("Starting....")
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print("Stop.")
