import pickle
import os
from build_database import (
    request_TRA_all_train_no_by_date, request_TRA_train_no_timetable_by_date,
    build_TRA_traintimetable, check_TRA_building_status_by_date,
)
from models import Base

FILENAME_FORMAT = "{0}-all-{1}-trains-timetable.pickle"


def create_new_TRA_example_by_date(date_input):
    outfile = open("tests/" + FILENAME_FORMAT.format(date_input.strftime("%Y-%m-%d"), "TRA"), "wb")
    all_train = request_TRA_all_train_no_by_date(date_input)
    try:
        for tn in all_train:
            timetable = request_TRA_train_no_timetable_by_date(tn, date_input)
            pickle.dump(timetable, outfile, pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        print(e)
        outfile.close()


class TimeTableExampleLoader(object):
    def __init__(self, date_input, train_type="TRA"):
        filename = FILENAME_FORMAT.format(date_input.strftime("%Y-%m-%d"),
                                          train_type)
        real_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 filename)
        if not os.path.exists(real_path):
            if train_type == "TRA":
                create_new_TRA_example_by_date(date_input)
        self.infile = open(real_path, "rb")

    def __enter__(self):
        return self

    def __iter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __next__(self):
        try:
            return pickle.load(self.infile)
        except EOFError:
            self.close()
            raise StopIteration

    def close(self):
        self.infile.close()


def load_example_timetable_to_database(session, date_input, train_type="TRA"):
    loader = TimeTableExampleLoader(date_input, train_type)
    if train_type == "TRA":
        check_TRA_building_status_by_date(date_input, session)
        for timetable in loader:
            build_TRA_traintimetable(timetable, session, date_input)
    session.commit()


def drop_all_table(engine):
    Base.metadata.drop_all(engine)
