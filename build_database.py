from utils import request_MOTC, convert_date_to_string
from datetime import datetime, date, timedelta
from models import TRA_Train, TRA_TrainTimeTable, TimeTableEntry
from sqlalchemy.orm.exc import NoResultFound
from data import TRA_STATION_CODE2NAME, TRA_TRAINTYPE_CODE2NAME

URL_FOR_ALL_TRAIN_NO_BY_DATE = "http://ptx.transportdata.tw/MOTC/v2/Rail/TRA/DailyTrainInfo/TrainDate/{0}"
URL_FOR_TRAIN_NO_TIMETABLE_BY_DATE = "http://ptx.transportdata.tw/MOTC/v2/Rail/TRA/DailyTimetable/TrainNo/{0}/TrainDate/{1}"


class ResponseMessage(object):
    """
    Define response messages in this class.
    The error message(except value 0) will be sent to line user.
    """
    status_dict = {
        0: "OK",
        1: "伺服端無法與平台連接",  # assign this value when an error happens in request_MOTC
        2: "沒有相關資料"  # when there is no result in response (empty)
    }

    def __init__(self, value):
        self.value = value

    def __str__(self):
        print("Response Type: {0}".format(self.message))

    @property
    def message(self):
        return self.status_dict[self.value]


def request_TRA_all_train_no_by_date(date_input):
    date_string = convert_date_to_string(date_input)
    url = URL_FOR_ALL_TRAIN_NO_BY_DATE.format(date_string)
    try:
        resp = request_MOTC(url)
    except Exception as e:
        print(e)
        return ResponseMessage(1)
    resp = resp.json()
    if not resp:
        return ResponseMessage(2)
    train_no_list = list()
    for entry in resp:
        train_no = entry["TrainNo"]
        train_no_list.append(train_no)
    return train_no_list


def request_TRA_train_no_timetable_by_date(train_no, date_input):
    """
    :return: the dictionary in the response or a error ResponseType
    """
    date_string = convert_date_to_string(date_input)
    url = URL_FOR_TRAIN_NO_TIMETABLE_BY_DATE.format(train_no, date_string)
    try:
        resp = request_MOTC(url)
    except Exception as e:
        print(e)
        return ResponseMessage(1)
    resp = resp.json()
    if not resp:
        return ResponseMessage(2)
    return resp[0]


def convert_TRA_traintype_code2name(traintype_code):
    return TRA_TRAINTYPE_CODE2NAME[traintype_code]


def convert_TRA_station_code2name(station_code):
    return TRA_STATION_CODE2NAME.get(station_code, None)


def build_TRA_traintimetable(timetable, session, date_input):
    # Create TRA_Train if not exist
    try:
        train = session.query(TRA_Train).filter_by(train_no=timetable["TrainNo"]).one()
    except NoResultFound:
        try:
            train_type_name = convert_TRA_traintype_code2name(timetable["TrainTypeCode"])
        except KeyError:
            print("Can't convert train_type_code: {}".format(timetable["TrainTypeCode"]))
            return False
        train = TRA_Train(timetable["TrainNo"], train_type_name)
        session.add(train)
    if not isinstance(date_input, date):
        raise TypeError("date_input is not a instance of date")

    # Create TRA_TrainTimeTable
    timetable = TRA_TrainTimeTable(date_input)
    timetable.train = train

    # Create a list of TimeTableEntry
    timetable_entrylist = list()
    cross_day = False
    for entry in timetable["StopTimes"]:
        try:
            station_name = convert_TRA_station_code2name(entry["StationID"])
        except KeyError:
            print("Can't convert station_code: {}".format(timetable["StationID"]))
            continue
        arrival_time = datetime.strptime(entry["ArrivalTime"], "%H:%M").time()
        departure_time = datetime.strptime(entry["DepartureTime"], "%H:%M").time()

        if cross_day:
            arrival_date = date_input + timedelta(1)
            departure_date = date_input + timedelta(1)
        elif departure_time < arrival_time:
            cross_day = True
            arrival_date = date_input
            departure_date = date_input + timedelta(1)
        else:
            arrival_date = departure_date = date_input

        table_entry = TimeTableEntry(
            station_name=station_name,
            arrival_time=datetime.combine(arrival_date, arrival_time),
            departure_time=datetime.combine(departure_date, departure_time)
        )
        timetable_entrylist.append(table_entry)

    timetable.timetable_entrylist = timetable_entrylist
    session.add(timetable)
    session.commit()


def build_TRA_DATABASE_by_date(date_input, session, ignore_built=False):
    """
    Call this function to build Time Table for all trains specified by date
    :param date_input: date object
    :param ignore_built: if ignore_built is True, then it will build the database anyway even if the database has already
    built on that day
    :return ResponseMessage
    """
    if isinstance(date_input, datetime):
        date_input = date_input.date()
    r = session.query(TRA_TrainTimeTable).filter_by(date=date_input)
    if not ignore_built and len(r) > 1:
        return ResponseMessage(0)
    response = request_TRA_all_train_no_by_date(date)
    if isinstance(response, ResponseMessage):
        return response
    else:
        train_no_list = response
    for train_no in train_no_list:
        response = request_TRA_train_no_timetable_by_date(train_no, date)
        if isinstance(response, ResponseMessage):
            return response
        train_timetable = response
        build_TRA_traintimetable(train_timetable, session, date_input)
    return ResponseMessage(0)
