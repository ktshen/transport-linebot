from sqlalchemy import Column, Integer, String, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref

Base = declarative_base()


class TimeTableEntry(Base):
    __tablename__ = "timetable_entry"

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
    departure_time = Column(DateTime)
    departure_station = Column(String(30))
    terminal_station = Column(String(30))

    def __init__(self, group, user, departure_time, departure_station, terminal_station):
        self.group = group
        self.user = user
        self.departure_time = departure_time
        self.departure_station = departure_station
        self.terminal_station = terminal_station

    def __repr__(self):
        return "QuestionState's id: {}".format(self.id)


class TRA_Train(Base):
    __tablename__ = 'tra_train'

    id = Column(Integer, primary_key=True)
    train_no = Column(String(5))
    train_type = Column(String(5))

    def __init__(self, train_no, train_type):
        self.train_no = train_no
        self.train_type = train_type


class TRA_TrainTimeTable(Base):
    __tablename__ = 'tra_traintimetable'

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    train_id = Column(Integer, ForeignKey('tra_train.id'))
    train = relationship("TRA_Train", backref=backref("traintimetable"))
    timetable_entry_id = Column(Integer, ForeignKey('timetable_entry.id'))
    timetable_entrylist = relationship("TimeTableEntry", backref=backref("tra_traintimetable"))

    def __init__(self, date):
        self.date = date
