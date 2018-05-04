from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref

Base = declarative_base()


class TableEntry(object):
    id = Column(Integer, primary_key=True)
    station_name = Column(String(10))
    arrival_time = Column(DateTime)
    departure_time = Column(DateTime)

    def __init__(self, station_name, arrival_time, departure_time):
        self.station_name = station_name
        self.arrival_time = arrival_time
        self.departure_time = departure_time


class TRA_QuestionState(Base):
    __tablename__ = 'tra_questionstate'

    id = Column(Integer, primary_key=True)
    group = Column(String(30))
    user = Column(String(30))
    departure_station = Column(String(30))
    destination_station = Column(String(30))
    departure_time = Column(DateTime)
    expired = Column(Boolean)
    update = Column(DateTime)

    def __init__(self, group, user, departure_station="", destination_station="", departure_time=None,
                 expired=False):
        self.group = group
        self.user = user
        self.departure_station = departure_station
        self.destination = destination_station
        self.departure_time = departure_time
        self.expired = expired

    def __repr__(self):
        return "QuestionState's id: {}".format(self.id)


class TRA_Train(Base):
    """
    1. This class represents each train according to its train number and train type.
    2. Every TRA_Train has only one TRA_TrainTimeTable on each dates and TRA_TrainTimeTable
    may vary from date to date.
    3. Call traintimetable attribute to access TRA_TrainTimeTable.
    """
    __tablename__ = 'tra_train'

    id = Column(Integer, primary_key=True)
    train_no = Column(String(5), unique=True)
    train_type = Column(String(5))

    def __init__(self, train_no, train_type):
        self.train_no = train_no
        self.train_type = train_type


class TRA_TrainTimeTable(Base):
    """
    Call ".entries' attribute to access TRA_TableEntry
    """
    __tablename__ = 'tra_traintimetable'

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    train_id = Column(Integer, ForeignKey('tra_train.id'))
    train = relationship("TRA_Train",
                         backref=backref("traintimetable", cascade="all, delete-orphan"))

    def __init__(self, date):
        self.date = date


class TRA_TableEntry(TableEntry, Base):
    __tablename__ = "tra_tableentry"

    timetable_id = Column(Integer, ForeignKey('tra_traintimetable.id'))
    timetable = relationship("TRA_TrainTimeTable",
                             backref=backref("entries", cascade="all, delete-orphan"))


class TRA_BuildingStatusOnDate(Base):
    """
    :param assigned_date : the date that this class is responsible for
    :param update_date : the latest update date
    :param status : 0: not built yet, 1: building, 2: built, 3: remove
    """
    __tablename__ = "tra_dataupdatestatus"

    id = Column(Integer, primary_key=True)
    assigned_date = Column(Date, unique=True)
    update_date = Column(Date)
    status = Column(Integer)

    def __init__(self, assigned_date, update_date=None, status=0):
        self.assigned_date = assigned_date
        self.update_date = update_date
        self.status = status
