import os
import time
from utils import convert_date_to_string
from dotenv import load_dotenv
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from build_database import build_TRA_Database_by_date, remove_TRA_timetable_by_date
from models import Base, TRA_BuildingStatusOnDate

# Load env variables
dotenv_path = os.path.join(os.getcwd(), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)

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
    2. make sure that data within a month has existed
    """
    today = datetime.now().date()
    for i in range(30):
        d = today + timedelta(i)
        ignore_built = True if i == 0 else False
        resp = build_TRA_Database_by_date(d, session, ignore_built)
        print("Update TRA DATABASE on {0}, result={1}".format(convert_date_to_string(d),
                                                              resp.message))


def clear_TRA_history():
    history_date = (datetime.now() - timedelta(1)).date()
    q = session.query(TRA_BuildingStatusOnDate) \
               .filter(TRA_BuildingStatusOnDate.assigned_date < history_date).all()
    if not q:
        return True
    for s in q:
        remove_TRA_timetable_by_date(s.assigned_date, session)


# 24-HOUR
RUN_JOBS_AT_TIME = "00:00"
# Specify periodic jobs here
JOB_QUEUE = [build_TRA, clear_TRA_history]


def main():
    invoked_time = datetime.strptime(RUN_JOBS_AT_TIME, "%H:%M").time()
    while True:
        time.sleep(60)
        now = datetime.now()
        if now.time() == invoked_time:
            print("Start Running Jobs at {0}".format(now.strftime("%Y-%m-%d %H:%M")))
            for job in JOB_QUEUE:
                try:
                    job()
                except Exception as e:
                    print(e)
                    pass


if __name__ == "__main__":
    try:
        print("Starting....")
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print("Stop.")
