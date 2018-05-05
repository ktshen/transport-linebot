import traceback
import sys
from utils import request_MOTC, convert_date_to_string
from datetime import datetime, date, timedelta
from sqlalchemy.orm.exc import NoResultFound

from models import TRA_Train, TRA_TrainTimeTable, TRA_TableEntry, TRA_BuildingStatusOnDate
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
        1: "伺服端無法與平台連接",    # assign this value when an error happens in request_MOTC
        2: "沒有相關資料",           # when there is no result in response (empty)
        3: "建構資料中，稍後再試",    # When a process has already been building the data
        9: "不知名錯誤",             # Unrecognised Error
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
        traceback.print_exc(file=sys.stdout)
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
        traceback.print_exc(file=sys.stdout)
        return ResponseMessage(1)
    resp = resp.json()
    if not resp:
        return ResponseMessage(2)
    return resp[0]


def convert_TRA_traintype_code2name(traintype_code):
    return TRA_TRAINTYPE_CODE2NAME[traintype_code]


def convert_TRA_station_code2name(station_code):
    return TRA_STATION_CODE2NAME.get(station_code, None)


def remove_TRA_timetable_by_date(date_input, session):
    q = session.query(TRA_TrainTimeTable).filter_by(date=date_input).all()
    if not q:
        return True
    for table in q:
        session.delete(table)
    update_TRA_building_status(date_input, 4, session)


def create_TRA_building_status_by_date(date_input, status, session):
    status_object = TRA_BuildingStatusOnDate(assigned_date=date_input,
                                             update_date=datetime.now().date(),
                                             status=status)
    session.add(status_object)
    session.commit()


def check_TRA_building_status_by_date(date_input, session):
    try:
        q = session.query(TRA_BuildingStatusOnDate).filter_by(assigned_date=date_input).one()
    except NoResultFound:
        create_TRA_building_status_by_date(date_input, 0, session)
        return 0
    return q.status


def update_TRA_building_status(date_input, status, session):
    try:
        status_object = session.query(TRA_BuildingStatusOnDate).filter_by(assigned_date=date_input).one()
    except NoResultFound:
        create_TRA_building_status_by_date(date_input, status, session)
        return True
    status_object.status = status
    status_object.update_date = datetime.now().date()
    session.commit()


def build_TRA_traintimetable(table_input, session, date_input):
    """
    table_input form:
    RailDailyTimetable {
        TrainDate (string): 行駛日期(格式: yyyy-MM-dd) ,
        DailyTrainInfo (RailDailyTrainInfo): 車次資料 ,
        StopTimes (Array[RailStopTime]): 停靠時間資料 ,
        UpdateTime (DateTime): 資料更新日期時間(ISO8601格式:yyyy-MM-ddTHH:mm:sszzz)
    }
    RailStopTime {
        StopSequence (integer): 跑法站序(由1開始) ,
        StationID (string): 車站代碼 ,
        StationName (NameType): 車站名稱 ,
        ArrivalTime (string): 到站時間(格式: HH:mm:ss) ,
        DepartureTime (string): 離站時間(格式: HH:mm:ss)
    }
    """
    # Create TRA_Train if not exist
    try:
        train = session.query(TRA_Train).filter_by(train_no=table_input["DailyTrainInfo"]["TrainNo"]).one()
    except NoResultFound:
        train_type_name = convert_TRA_traintype_code2name(table_input["DailyTrainInfo"]["TrainTypeCode"])
        train = TRA_Train(table_input["DailyTrainInfo"]["TrainNo"], train_type_name)
        session.add(train)
    # Update TRA_BuildingStatusOnDate for the date with status building
    update_TRA_building_status(date_input, 1, session)
    # Create TRA_TrainTimeTable
    timetable = TRA_TrainTimeTable(date_input)
    timetable.train = train
    # Create a list of TimeTableEntry
    cross_day = False
    previous_departure_time = None
    for entry in table_input["StopTimes"]:
        try:
            station_name = convert_TRA_station_code2name(entry["StationID"])
        except KeyError:
            print("Can't convert station_code: {}".format(entry["StationID"]))
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
        elif previous_departure_time and arrival_time < previous_departure_time:
            cross_day = True
            arrival_date = departure_date = date_input + timedelta(1)
        else:
            arrival_date = departure_date = date_input

        table_entry = TRA_TableEntry(
            station_name=station_name,
            arrival_time=datetime.combine(arrival_date, arrival_time),
            departure_time=datetime.combine(departure_date, departure_time)
        )
        timetable.entries.append(table_entry)
        previous_departure_time = departure_time
    session.add(timetable)
    update_TRA_building_status(date_input, 2, session)


def build_TRA_Database_by_date(date_input, session, ignore_built=False):
    """
    Call this function to build Time Table for all trains specified by date
    :param date_input: date object
    :param ignore_built: if ignore_built is True, then it will build the database anyway even if the database has already
    built on that day
    :return ResponseMessage
    """
    try:
        if isinstance(date_input, datetime):
            date_input = date_input.date()
        elif not isinstance(date_input, date):
            raise TypeError("Need a date object.")
        building_status = check_TRA_building_status_by_date(date_input, session)
        if not ignore_built and building_status == 2:
            return ResponseMessage(0)
        elif building_status == 1:
            return ResponseMessage(3)

        # Get a list of train no on specified date
        response = request_TRA_all_train_no_by_date(date_input)
        if isinstance(response, ResponseMessage):
            return response
        else:
            train_no_list = response

        # Remove the older data and build the database
        remove_TRA_timetable_by_date(date_input, session)
        for train_no in train_no_list:
            response = request_TRA_train_no_timetable_by_date(train_no, date_input)
            if isinstance(response, ResponseMessage):
                return response
            train_timetable = response
            build_TRA_traintimetable(train_timetable, session, date_input)
        session.commit()
        return ResponseMessage(0)
    except Exception as e:
        remove_TRA_timetable_by_date(date_input, session)
        traceback.print_exc(file=sys.stdout)
        return ResponseMessage(9)
