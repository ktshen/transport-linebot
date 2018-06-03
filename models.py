from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref

Base = declarative_base()


class TableEntry(object):
    id = Column(Integer, primary_key=True)
    station_name = Column(String(50))
    arrival_time = Column(DateTime)
    departure_time = Column(DateTime)

    def __init__(self, station_name, arrival_time, departure_time):
        self.station_name = station_name
        self.arrival_time = arrival_time
        self.departure_time = departure_time


class QuestionState(object):
    id = Column(Integer, primary_key=True)
    group = Column(String(100))
    user = Column(String(100))
    departure_station = Column(String(100))
    destination_station = Column(String(100))
    departure_time = Column(DateTime)
    expired = Column(Boolean)
    update = Column(DateTime)

    def __init__(self, group, user, departure_station="", destination_station="", departure_time=None,
                 expired=False):
        self.group = group
        self.user = user
        self.departure_station = departure_station
        self.destination_station = destination_station
        self.departure_time = departure_time
        self.expired = expired
        self.update = datetime.now()


class BuildingStatusOnDate(object):
    """
        :param assigned_date : the date that this class is responsible for
        :param update_date : the latest update date
        :param status : 0: not built yet, 1: building, 2: built, 3: remove
    """

    id = Column(Integer, primary_key=True)
    assigned_date = Column(Date, unique=True)
    update_date = Column(Date)
    status = Column(Integer)

    def __init__(self, assigned_date, update_date=None, status=0):
        self.assigned_date = assigned_date
        self.update_date = update_date
        self.status = status


class TRA_QuestionState(QuestionState, Base):
    __tablename__ = 'tra_questionstate'

    def __repr__(self):
        return "TRA_QuestionState's id: {}".format(self.id)


class TRA_Train(Base):
    """
    1. This class represents each train according to its train number and train type.
    2. Every TRA_Train has only one TRA_TrainTimeTable on each dates and TRA_TrainTimeTable
    may vary from date to date.
    3. Call traintimetable attribute to access TRA_TrainTimeTable.
    """
    __tablename__ = 'tra_train'

    id = Column(Integer, primary_key=True)
    train_no = Column(String(10), unique=True)
    train_type = Column(String(10))

    def __init__(self, train_no, train_type):
        self.train_no = train_no
        self.train_type = train_type


class TRA_TrainTimeTable(Base):
    """
    Call ".entries" attribute to access TRA_TableEntry
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
                             backref=backref("entries",
                                             cascade="all, delete-orphan",
                                             order_by='TRA_TableEntry.arrival_time'))


class TRA_BuildingStatusOnDate(BuildingStatusOnDate, Base):
    __tablename__ = "tra_dataupdatestatus"


class THSR_QuestionState(QuestionState, Base):
    __tablename__ = 'thsr_questionstate'

    def __repr__(self):
        return "THSR_QuestionState's id: {}".format(self.id)


class THSR_Train(Base):
    __tablename__ = 'thsr_train'

    id = Column(Integer, primary_key=True)
    train_no = Column(String(10), unique=True)

    def __init__(self, train_no):
        self.train_no = train_no


class THSR_TrainTimeTable(Base):
    __tablename__ = 'thsr_traintimetable'

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    train_id = Column(Integer, ForeignKey('thsr_train.id'))
    train = relationship("THSR_Train",
                         backref=backref("traintimetable", cascade="all, delete-orphan"))

    def __init__(self, date):
        self.date = date


class THSR_TableEntry(TableEntry, Base):
    __tablename__ = "thsr_tableentry"

    timetable_id = Column(Integer, ForeignKey('thsr_traintimetable.id'))
    timetable = relationship("THSR_TrainTimeTable",
                             backref=backref("entries",
                                             cascade="all, delete-orphan",
                                             order_by='THSR_TableEntry.arrival_time'))


class THSR_BuildingStatusOnDate(BuildingStatusOnDate, Base):
    __tablename__ = "thsr_dataupdatestatus"


"""
User and group might follow and then unfollow and follow and so on repeatedly,
so don't make user_id and group_id unique.
Consider these classes as a method of recording User's and Group's activity.
"""
class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    user_id = Column(String(100))
    following = Column(Boolean)
    follow_datetime = Column(DateTime)
    unfollow_datetime = Column(DateTime)

    def __init__(self, user_id):
        self.user_id = user_id
        self.following = True
        self.follow_datetime = datetime.now()
        self.unfollow_datetime = None


class Group(Base):
    __tablename__ = 'group'

    id = Column(Integer, primary_key=True)
    group_id = Column(String(100))
    joinning = Column(Boolean)
    join_datetime = Column(DateTime)
    leave_datetime = Column(DateTime)

    def __init__(self, group_id):
        self.group_id = group_id
        self.joinning = True
        self.join_datetime = datetime.now()
        self.leave_datetime = None
