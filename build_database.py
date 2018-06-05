import traceback
import sys
from utils import request_MOTC, convert_date_to_string
from datetime import datetime, date, timedelta
from sqlalchemy.orm.exc import NoResultFound

from models import (
    TRA_Train, TRA_TrainTimeTable, TRA_TableEntry, TRA_BuildingStatusOnDate,
    THSR_Train, THSR_TrainTimeTable, THSR_TableEntry, THSR_BuildingStatusOnDate
)
from data import (
    TRA_STATION_CODE2NAME, TRA_TRAINTYPE_CODE2NAME, THSR_STATION_CODE2NAME
)

URL_FOR_ALL_TRA_TRAIN_NO_AND_TIMETABLE = "http://ptx.transportdata.tw/MOTC/v2/Rail/TRA/DailyTimetable/TrainDate/{0}"
URL_FOR_ALL_THSR_TRAIN_NO_AND_TIMETABLE = "http://ptx.transportdata.tw/MOTC/v2/Rail/THSR/DailyTimetable/TrainDate/{0}"


class ResponseMessage(object):
    """
    Define response messages in this class.
    The error message(except value 0) will be sent to line user.
    """
    status_dict = {
        0: "OK",
        1: "伺服端無法與平台連接",    # assign this value when an error happens in request_MOTC
        2: "取得資訊為空白",         # when there is no result in response (empty)
        3: "建構資料中，稍後再試",    # When a process has already been building the data
        9: "不知名錯誤",             # Unrecognised Error
        10: "",                     # Self defined Error
    }

    def __init__(self, value, message=""):
        self.value = value
        if value == 10:
            self.status_dict[self.value] = message

    def __str__(self):
        print("Response Type: {0}".format(self.message))

    @property
    def message(self):
        return self.status_dict[self.value]


def request_TRA_all_train_timetable_by_date(date_input):
    date_string = convert_date_to_string(date_input)
    url = URL_FOR_ALL_TRA_TRAIN_NO_AND_TIMETABLE.format(date_string)
    try:
        resp = request_MOTC(url)
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return ResponseMessage(1)
    if not resp:
        return ResponseMessage(2)
    elif "message" in resp:
        return ResponseMessage(10, resp["message"])
    return resp


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
    update_TRA_building_status(date_input, 3, session)


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


def build_TRA_database_by_date(date_input, session, build_anyway=False):
    """
    Call this function to build Time Table for all trains specified by date
    :param date_input: date object
    :param build_anyway: if build_anyway is True, then it will build the database anyway even if the database has
    already built on that day
    :return ResponseMessage
    """
    try:
        if isinstance(date_input, datetime):
            date_input = date_input.date()
        elif not isinstance(date_input, date):
            raise TypeError("Need a date object.")
        # This will create a new TRA_BuildingStatusOnDate with status 0 if not exists
        building_status = check_TRA_building_status_by_date(date_input, session)
        if not build_anyway and building_status == 2:
            return ResponseMessage(0)
        # We assume that only one process is running all the time. So there is no competitive problem
        # The status is 1 because it is terminated while running previously
        elif building_status == 1:
            pass

        # Get a list of train no on specified date
        response = request_TRA_all_train_timetable_by_date(date_input)
        if isinstance(response, ResponseMessage):
            return response
        else:
            all_trains = response
        # Remove the older data and build the database
        remove_TRA_timetable_by_date(date_input, session)
        for tb in all_trains:
            build_TRA_traintimetable(tb, session, date_input)
        session.commit()
        return ResponseMessage(0)
    except Exception as e:
        remove_TRA_timetable_by_date(date_input, session)
        traceback.print_exc(file=sys.stdout)
        return ResponseMessage(9)


################################### THSR below ##################################


def create_THSR_building_status_by_date(date_input, status, session):
    status_object = THSR_BuildingStatusOnDate(assigned_date=date_input,
                                              update_date=datetime.now().date(),
                                              status=status)
    session.add(status_object)
    session.commit()


def check_THSR_building_status_by_date(date_input, session):
    try:
        q = session.query(THSR_BuildingStatusOnDate).filter_by(assigned_date=date_input).one()
    except NoResultFound:
        create_THSR_building_status_by_date(date_input, 0, session)
        return 0
    return q.status


def update_THSR_building_status(date_input, status, session):
    try:
        status_object = session.query(THSR_BuildingStatusOnDate).filter_by(assigned_date=date_input).one()
    except NoResultFound:
        create_THSR_building_status_by_date(date_input, status, session)
        return True
    status_object.status = status
    status_object.update_date = datetime.now().date()
    session.commit()


def remove_THSR_timetable_by_date(date_input, session):
    q = session.query(THSR_TrainTimeTable).filter_by(date=date_input).all()
    if not q:
        return True
    for table in q:
        session.delete(table)
    update_THSR_building_status(date_input, 3, session)


def request_THSR_all_train_timetable(date_input):
    """
    :return: a list of RailDailyTimetable
    """
    date_string = convert_date_to_string(date_input)
    url = URL_FOR_ALL_THSR_TRAIN_NO_AND_TIMETABLE.format(date_string)
    try:
        resp = request_MOTC(url)
    except:
        traceback.print_exc(file=sys.stdout)
        return ResponseMessage(1)
    if not resp:
        return ResponseMessage(2)
    elif "message" in resp:
        return ResponseMessage(10, resp["message"])
    return resp


def convert_THSR_station_code2name(station_id):
    return THSR_STATION_CODE2NAME[station_id]


def build_THSR_traintimetable(table_input, session, date_input):
    """
    table_input form:
    RailDailyTimetable {
        TrainDate (string): 行駛日期(格式: yyyy:MM:dd) ,
        DailyTrainInfo (RailDailyTrainInfo): 車次資料 ,
        StopTimes (Array[RailStopTime]): 停靠時間資料 ,
        UpdateTime (DateTime): 資料更新日期時間
    }
    RailDailyTrainInfo {
        TrainNo (string): 車次代碼 ,
        Direction (string): 行駛方向 = ['0: 南下', '1: 北上'],
        StartingStationID (string, optional): 列車起點車站代號 ,
        StartingStationName (NameType, optional): 列車起點車站名稱 ,
        EndingStationID (string, optional): 列車終點車站代號 ,
        EndingStationName (NameType, optional): 列車終點車站名稱 ,
        Note (NameType, optional): 附註說明
    }
    RailStopTime {
        StopSequence (integer): 跑法站序(由1開始) ,
        StationID (string): 車站代碼 ,
        StationName (NameType): 車站名稱 ,
        ArrivalTime (string, optional): 到站時間(格式: HH:mm:ss) ,
        DepartureTime (string): 離站時間(格式: HH:mm:ss)
    }
    """
    # Create TRA_Train if not exist
    train_no = table_input["DailyTrainInfo"]["TrainNo"]
    try:
        train = session.query(THSR_Train).filter_by(train_no=train_no).one()
    except NoResultFound:
        train = THSR_Train(train_no)
        session.add(train)
    # Update THSR_BuildingStatusOnDate for the date with status building
    update_THSR_building_status(date_input, 1, session)
    # Create THSR_TrainTimeTable
    timetable = THSR_TrainTimeTable(date_input)
    timetable.train = train

    # Create a list of TimeTableEntry
    cross_day = False
    previous_departure_time = None
    for entry in table_input["StopTimes"]:
        try:
            station_name = convert_THSR_station_code2name(entry["StationID"])
        except KeyError:
            print("Can't convert station_code: {}".format(entry["StationID"]))
            continue
        departure_time = datetime.strptime(entry["DepartureTime"], "%H:%M").time()
        try:
            arrival_time = datetime.strptime(entry["ArrivalTime"], "%H:%M").time()
        except KeyError:
            arrival_time = departure_time

        if cross_day:
            arrival_date = departure_date = date_input + timedelta(1)
        elif departure_time < arrival_time:
            cross_day = True
            arrival_date = date_input
            departure_date = date_input + timedelta(1)
        elif previous_departure_time and arrival_time < previous_departure_time:
            cross_day = True
            arrival_date = departure_date = date_input + timedelta(1)
        else:
            arrival_date = departure_date = date_input

        table_entry = THSR_TableEntry(
            station_name=station_name,
            arrival_time=datetime.combine(arrival_date, arrival_time),
            departure_time=datetime.combine(departure_date, departure_time)
        )
        timetable.entries.append(table_entry)
        previous_departure_time = departure_time
    session.add(timetable)
    update_THSR_building_status(date_input, 2, session)


def build_THSR_database_by_date(date_input, session, build_anyway=False):
    try:
        if isinstance(date_input, datetime):
            date_input = date_input.date()
        elif not isinstance(date_input, date):
            raise TypeError("Need a date object.")
        # This will create a new THSR_BuildingStatusOnDate with status 0 if not exists
        # We assume that only one process is running all the time. So there is no competitive problem
        # so if the status is 1, it is probably terminated while running previously
        building_status = check_THSR_building_status_by_date(date_input, session)
        if not build_anyway and building_status == 2:
            return ResponseMessage(0)
        # Get a list of train no on specified date
        response = request_THSR_all_train_timetable(date_input)
        if isinstance(response, ResponseMessage):
            return response
        # Remove the older data and build the database
        remove_THSR_timetable_by_date(date_input, session)
        for train in response:
            build_THSR_traintimetable(train, session, date_input)
        session.commit()
        return ResponseMessage(0)
    except:
        remove_THSR_timetable_by_date(date_input, session)
        traceback.print_exc(file=sys.stdout)
        return ResponseMessage(9)
