import unittest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .load_example import load_example_timetable_to_database, remove_example_from_database

from models import Base
from handlers import *
from app import app

engine = create_engine(os.environ["DATABASE_URI"])
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
TEST_DATE = datetime(2018, 6, 2)


class TestCase_for_request_TRA_matching_train(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        session = Session()
        load_example_timetable_to_database(session, TEST_DATE)

    @classmethod
    def tearDownClass(cls):
        session = Session()
        load_example_timetable_to_database(session, TEST_DATE)
        remove_example_from_database(session, TEST_DATE)

    def setUp(self):
        self.app = app
        self.app.session = Session()

    def check(self, correct_list, result):
        for i in range(len(result)):
            _l = result[i]
            ans = [_l[0].train.train_no, _l[0].train.train_type,
                   _l[1].departure_time.strftime("%H:%M"),
                   _l[2].arrival_time.strftime("%H:%M")]
            self.assertEqual(ans, correct_list[i])

    def test_case_1(self):
        correct_list = [['51', '莒光', '07:19', '11:16'], ['103', '自強', '07:40', '11:32'],
                        ['105', '自強', '08:14', '12:10'], ['507', '莒光', '08:53', '14:15'],
                        ['113', '自強', '09:38', '13:21'], ['115', '自強', '10:13', '13:53'],
                        ['511', '莒光', '10:54', '15:49'], ['117', '自強', '11:05', '14:51'],
                        ['121', '自強', '12:10', '16:00'], ['513', '莒光', '12:49', '18:01'],
                        ['123', '自強', '13:10', '16:50'], ['125', '自強', '14:13', '17:50'],
                        ['129', '自強', '15:08', '18:49'], ['561', '莒光', '15:20', '20:38'],
                        ['133', '自強', '15:33', '18:15'], ['135', '自強', '16:10', '19:54'],
                        ['175', '自強', '17:10', '20:58'], ['521', '莒光', '17:46', '22:59'],
                        ['139', '自強', '18:10', '21:51'], ['141', '自強', '18:40', '22:24'],
                        ['145', '自強', '19:20', '23:06'], ['149', '自強', '19:56', '23:47'],
                        ['181', '自強', '20:37', '00:17']]

        with self.app.app_context():
            qs = TRA_QuestionState(group=None, user='123',
                                   departure_station="新竹",
                                   destination_station="高雄",
                                   departure_time=datetime(2018, 6, 2, 7, 0))
            res = request_TRA_matching_train(qs)
            for i in range(len(res)):
                _l = res[i]
                ans = [_l[0].train.train_no, _l[0].train.train_type,
                       _l[1].departure_time.strftime("%H:%M"),
                       _l[2].arrival_time.strftime("%H:%M")]
                self.assertEqual(ans, correct_list[i])

    def test_case_2(self):
        correct_list = [['1272', '區間', '22:19', '22:23'], ['2254', '區間', '22:37', '22:41'],
                        ['1278', '區間', '23:12', '23:16'], ['1274', '區間', '23:28', '23:32'],
                        ['1284', '區間', '23:57', '00:01']]
        with self.app.app_context():
            qs = TRA_QuestionState(group=None, user='123',
                                   departure_station="鶯歌",
                                   destination_station="山佳",
                                   departure_time=datetime(2018, 6, 2, 22, 0))
            res = request_TRA_matching_train(qs)
            self.check(correct_list, res)

    def test_case_3(self):
        correct_list = [['105', '自強', '06:15', '11:02'], ['115', '自強', '08:14', '12:49'],
                        ['117', '自強', '09:06', '13:43'], ['129', '自強', '13:14', '17:44']]

        with self.app.app_context():
            qs = TRA_QuestionState(group=None, user='123',
                                   departure_station="基隆",
                                   destination_station="新營",
                                   departure_time=datetime(2018, 6, 2, 6, 0))
            res = request_TRA_matching_train(qs)
            self.check(correct_list, res)

    def test_case_4(self):
        correct_list = [['1804', '區間', '07:09', '07:38'], ['1806', '區間', '08:07', '08:38'],
                        ['1808', '區間', '08:57', '09:34'], ['1812', '區間', '10:03', '10:34'],
                        ['1814', '區間', '11:03', '11:34'], ['1816', '區間', '12:03', '12:34'],
                        ['1818', '區間', '13:03', '13:34'], ['1822', '區間', '14:03', '14:34'],
                        ['1824', '區間', '15:03', '15:34'], ['1826', '區間', '16:03', '16:34'],
                        ['1828', '區間', '17:03', '17:34'], ['1832', '區間', '18:03', '18:34'],
                        ['1836', '區間', '19:03', '19:34'], ['1838', '區間', '20:03', '20:34'],
                        ['1842', '區間', '22:03', '22:34']]
        with self.app.app_context():
            qs = TRA_QuestionState(group=None, user='123',
                                   departure_station="榮華",
                                   destination_station="內灣",
                                   departure_time=datetime(2018, 6, 2, 6, 0))
            res = request_TRA_matching_train(qs)
            self.check(correct_list, res)

    def test_case_5(self):
        correct_list = [['1803', '區間', '06:18', '06:30'], ['1805', '區間', '07:51', '08:03'],
                        ['1807', '區間', '08:51', '09:03'], ['1811', '區間', '09:51', '10:03'],
                        ['1813', '區間', '10:51', '11:03'], ['1815', '區間', '11:51', '12:03'],
                        ['1817', '區間', '12:51', '13:03'], ['1821', '區間', '13:51', '14:03'],
                        ['1823', '區間', '14:51', '15:03'], ['1825', '區間', '15:51', '16:03'],
                        ['1827', '區間', '16:51', '17:03'], ['1833', '區間', '17:51', '18:03'],
                        ['1835', '區間', '18:51', '19:03'], ['1839', '區間', '19:51', '20:03'],
                        ['1841', '區間', '20:51', '21:03']]
        with self.app.app_context():
            qs = TRA_QuestionState(group=None, user='123',
                                   departure_station="富貴",
                                   destination_station="橫山",
                                   departure_time=datetime(2018, 6, 2, 6, 0))
            res = request_TRA_matching_train(qs)
            self.check(correct_list, res)