import unittest
from unittest.mock import MagicMock
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from linebot.models import PostbackEvent, TemplateSendMessage

from .load_example import load_example_timetable_to_database, drop_all_table
from models import (
    Base, TRA_QuestionState, THSR_QuestionState, User, Group
)
from handlers import (
    request_TRA_matching_train, request_THSR_matching_train, ask_question_states,
    handle_follow_event, handle_join_event, handle_unfollow_event,
    handle_leave_event, match_text_and_assign
)
from app import app

engine = create_engine(os.environ["TESTING_DATABASE_URI"])
Session = sessionmaker(bind=engine)
TEST_DATE_1 = datetime(2018, 6, 2)
TEST_DATE_2 = datetime(2018, 6, 5)


class BaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(engine)

    @classmethod
    def tearDownClass(cls):
        drop_all_table(engine)

    def setUp(self):
        self.app = app
        self.app.session = Session()

    def tearDown(self):
        self.app.session.query(TRA_QuestionState).delete()
        self.app.session.query(THSR_QuestionState).delete()
        self.app.session.commit()
        self.app.session.close()


class BaseTRATestCase(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        session = Session()
        load_example_timetable_to_database(session, TEST_DATE_1)


class TestCase_for_request_TRA_matching_train(BaseTRATestCase):
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
            self.check(correct_list, res)

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


class TestCase_for_ask_TRA_question_states(BaseTRATestCase):
    def test_multiple_question_states_exists(self):
        mock_event = MagicMock()
        mock_event.source.user_id = mock_event.source.group_id = user_id = group = "123"
        # Create two questions states
        qs_1 = TRA_QuestionState(group=group, user=user_id)
        self.app.session.add(qs_1)
        qs_2 = TRA_QuestionState(group=group, user=user_id)
        self.app.session.add(qs_2)
        with self.app.app_context():
            result = ask_question_states(mock_event)
            # Should return None and expire all question states
            self.assertIsNone(result)
            q = self.app.session.query(TRA_QuestionState).all()
            self.assertEqual(len(q), 2)
            for i in q:
                self.assertEqual(i.expired, True)

    def test_message_choosing_departure_station(self):
        mock_event = MagicMock()
        mock_event.source.user_id = mock_event.source.group_id = user_id = group = "123"
        mock_event.message.text = "新竹"
        qs_1 = TRA_QuestionState(group=group, user=user_id)
        self.app.session.add(qs_1)
        with self.app.app_context():
            result = ask_question_states(mock_event)
            self.assertEqual(result.text, "請輸入目的站")

    def test_message_choosing_destination_station(self):
        mock_event = MagicMock()
        mock_event.source.user_id = mock_event.source.group_id = user_id = group = "123"
        mock_event.message.text = "高雄"
        qs_1 = TRA_QuestionState(group=group, user=user_id,
                                 departure_station="新竹")
        self.app.session.add(qs_1)
        with self.app.app_context():
            result = ask_question_states(mock_event)
            self.assertEqual(result.alt_text, "請選擇搭乘時間")

    def test_destination_station_is_same_with_departure_station(self):
        mock_event = MagicMock()
        mock_event.source.user_id = mock_event.source.group_id = user_id = group = "123"
        mock_event.message.text = "新竹"
        qs_1 = TRA_QuestionState(group=group, user=user_id,
                                 departure_station="新竹")
        self.app.session.add(qs_1)
        with self.app.app_context():
            result = ask_question_states(mock_event)
            self.assertEqual(result.text, "輸入的目的站與起程站皆是新竹，請重新輸入有效目的站")

    def test_message_choosing_datetime(self):
        correct_items_in_result = ['0051', '莒光', '07:19', '11:16', '0103', '自強', '07:40', '11:32', '0105', '自強',
                                   '08:14', '12:10', '0507', '莒光', '08:53', '14:15']

        event = PostbackEvent()
        mock_source = MagicMock()
        mock_source.user_id = mock_source.group_id = user_id = group = "123"
        event.source = mock_source
        mock_postback = MagicMock()
        mock_postback.params = {"datetime": "2018-06-02T07:00"}
        event.postback = mock_postback
        qs_1 = TRA_QuestionState(group=group, user=user_id,
                                 departure_station="新竹",
                                 destination_station="高雄")
        self.app.session.add(qs_1)
        with self.app.app_context():
            result = ask_question_states(event)
            for item in correct_items_in_result:
                self.assertIn(item, result.template.text)


class TestCase_for_follow_unfollow_join_joinning_event(BaseTestCase):
    def clean_user_table(self):
        self.app.session.query(User).delete()

    def clean_group_table(self):
        self.app.session.query(Group).delete()

    def tearDown(self):
        self.clean_user_table()
        self.clean_group_table()
        super().tearDown()

    def test_follow_event_has_create_user(self):
        mock_event = MagicMock()
        mock_event.source.user_id = mock_event.reply_token = "123"
        with self.app.app_context():
            handle_follow_event(mock_event)
        q = self.app.session.query(User).one()
        self.assertEqual(q.user_id, "123")

    def test_unfollow_event_has_remove_user(self):
        user = User("123")
        self.app.session.add(user)
        mock_event = MagicMock()
        mock_event.source.user_id = "123"
        with self.app.app_context():
            handle_unfollow_event(mock_event)
        result = self.app.session.query(User).one()
        self.assertEqual(result.user_id, "123")
        self.assertFalse(result.following)
        self.assertIsNotNone(result.unfollow_datetime)

    def test_join_event_has_create_group(self):
        mock_event = MagicMock()
        mock_event.source.group_id = mock_event.reply_token = "123"
        with self.app.app_context():
            handle_join_event(mock_event)
        q = self.app.session.query(Group).one()
        self.assertEqual(q.group_id, "123")

    def test_leave_event_has_remove_group(self):
        group = Group("123")
        self.app.session.add(group)
        mock_event = MagicMock()
        mock_event.source.group_id = "123"
        with self.app.app_context():
            handle_leave_event(mock_event)
        result = self.app.session.query(Group).one()
        self.assertEqual(result.group_id, "123")
        self.assertFalse(result.joinning)
        self.assertIsNotNone(result.leave_datetime)


class BaseTHSRTestCase(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        session = Session()
        load_example_timetable_to_database(session, TEST_DATE_2, "THSR")


class TestCase_for_request_THSR_matching_train(BaseTHSRTestCase):
    def check(self, correct_list, result):
        for i in range(len(result)):
            _l = result[i]
            ans = [_l[0].train.train_no,
                   _l[1].departure_time.strftime("%H:%M"),
                   _l[2].arrival_time.strftime("%H:%M")]
            self.assertEqual(ans, correct_list[i])

    def test_case_1(self):
        correct_list = [['0803', '07:02', '08:40'],
                        ['0603', '07:27', '08:50'],
                        ['0805', '07:47', '09:25'],
                        ['0609', '08:22', '09:45'],
                        ['0809', '08:47', '10:25'],
                        ['0613', '08:56', '10:20'],
                        ['0615', '09:22', '10:45'],
                        ['0813', '09:47', '11:25'],
                        ['0619', '09:56', '11:20'],
                        ['0621', '10:22', '11:45'],
                        ['0817', '10:47', '12:25'],
                        ['0625', '10:56', '12:20'],
                        ['0627', '11:22', '12:45'],
                        ['0821', '11:47', '13:25'],
                        ['0633', '12:22', '13:45'],
                        ['0825', '12:47', '14:25'],
                        ['0639', '13:22', '14:45'],
                        ['0829', '13:47', '15:25'],
                        ['0645', '14:22', '15:45'],
                        ['0833', '14:47', '16:25'],
                        ['0651', '15:22', '16:45'],
                        ['0837', '15:47', '17:25'],
                        ['0657', '16:22', '17:45'],
                        ['0841', '16:47', '18:25'],
                        ['0661', '16:56', '18:20'],
                        ['0663', '17:22', '18:45'],
                        ['0845', '17:47', '19:25'],
                        ['0667', '17:56', '19:20'],
                        ['0669', '18:22', '19:45'],
                        ['0849', '18:47', '20:25'],
                        ['0673', '18:56', '20:20'],
                        ['0675', '19:22', '20:45'],
                        ['0853', '19:47', '21:25'],
                        ['0681', '20:22', '21:45'],
                        ['0857', '20:47', '22:25'],
                        ['0687', '21:22', '22:45'],
                        ['0861', '21:47', '23:25'],
                        ['0693', '22:17', '23:40']]

        with self.app.app_context():
            qs = THSR_QuestionState(group=None, user='123',
                                    departure_station="新竹",
                                    destination_station="左營",
                                    departure_time=datetime(2018, 6, 5, 7, 0))
            res = request_THSR_matching_train(qs)
            self.check(correct_list, res)

    def test_case_2(self):
        correct_list = [['0621', '10:22', '11:32'], ['0817', '10:47', '12:11'], ['0625', '10:56', '12:06'],
                        ['0627', '11:22', '12:32'], ['0821', '11:47', '13:11'], ['0633', '12:22', '13:32'],
                        ['0825', '12:47', '14:11'], ['0639', '13:22', '14:32'], ['0829', '13:47', '15:11'],
                        ['0645', '14:22', '15:32'], ['0833', '14:47', '16:11'], ['0651', '15:22', '16:32'],
                        ['0837', '15:47', '17:11'], ['0657', '16:22', '17:32'], ['0841', '16:47', '18:11'],
                        ['0661', '16:56', '18:06'], ['0663', '17:22', '18:32'], ['0845', '17:47', '19:11'],
                        ['0667', '17:56', '19:06'], ['0669', '18:22', '19:32'], ['0849', '18:47', '20:11'],
                        ['0673', '18:56', '20:06'], ['0675', '19:22', '20:32'], ['0853', '19:47', '21:11'],
                        ['0681', '20:22', '21:32'], ['0857', '20:47', '22:11'], ['0687', '21:22', '22:32'],
                        ['0861', '21:47', '23:11'], ['0693', '22:17', '23:27']]

        with self.app.app_context():
            qs = THSR_QuestionState(group=None, user='123',
                                    departure_station="新竹",
                                    destination_station="臺南",
                                    departure_time=datetime(2018, 6, 5, 10, 0))
            res = request_THSR_matching_train(qs)
            self.check(correct_list, res)


class TestCase_for_ask_THSR_question_states(BaseTHSRTestCase):
    def test_multiple_question_states_exists(self):
        mock_event = MagicMock()
        mock_event.source.user_id = mock_event.source.group_id = user_id = group = "123"
        # Create two questions states
        qs_1 = THSR_QuestionState(group=group, user=user_id)
        self.app.session.add(qs_1)
        qs_2 = THSR_QuestionState(group=group, user=user_id)
        self.app.session.add(qs_2)
        with self.app.app_context():
            result = ask_question_states(mock_event)
            # Should return None and expire all question states
            self.assertIsNone(result)
            q = self.app.session.query(THSR_QuestionState).all()
            self.assertEqual(len(q), 2)
            for i in q:
                self.assertEqual(i.expired, True)

    def test_message_choosing_departure_station(self):
        mock_event = MagicMock()
        mock_event.source.user_id = mock_event.source.group_id = user_id = group = "123"
        mock_event.message.text = "新竹"
        qs_1 = THSR_QuestionState(group=group, user=user_id)
        self.app.session.add(qs_1)
        with self.app.app_context():
            result = ask_question_states(mock_event)
            self.assertEqual(result.text, "請輸入目的站")

    def test_message_choosing_destination_station(self):
        mock_event = MagicMock()
        mock_event.source.user_id = mock_event.source.group_id = user_id = group = "123"
        mock_event.message.text = "左營"
        qs_1 = THSR_QuestionState(group=group, user=user_id,
                                  departure_station="新竹")
        self.app.session.add(qs_1)
        with self.app.app_context():
            result = ask_question_states(mock_event)
            self.assertEqual(result.alt_text, "請選擇搭乘時間")

    def test_destination_station_is_same_with_departure_station(self):
        mock_event = MagicMock()
        mock_event.source.user_id = mock_event.source.group_id = user_id = group = "123"
        mock_event.message.text = "新竹"
        qs_1 = THSR_QuestionState(group=group, user=user_id, departure_station="新竹")
        self.app.session.add(qs_1)
        with self.app.app_context():
            result = ask_question_states(mock_event)
            self.assertEqual(result.text, "輸入的目的站與起程站皆是新竹，請重新輸入有效目的站")

    def test_message_choosing_datetime(self):
        correct_items_in_result = ['0803', '07:02', '07:30', '0603', '07:27', '07:51', '0805', '07:47', '08:15', '1505',
                                   '08:12', '08:42']

        event = PostbackEvent()
        mock_source = MagicMock()
        mock_source.user_id = mock_source.group_id = user_id = group = "123"
        event.source = mock_source
        mock_postback = MagicMock()
        mock_postback.params = {"datetime": "2018-06-05T07:00"}
        event.postback = mock_postback
        qs_1 = THSR_QuestionState(group=group, user=user_id,
                                  departure_station="新竹",
                                  destination_station="臺中")
        self.app.session.add(qs_1)
        with self.app.app_context():
            result = ask_question_states(event)
            for item in correct_items_in_result:
                self.assertIn(item, result.template.text)


class TestCase_for_match_text_and_assign(BaseTestCase):
    def test_request_main_menu(self):
        mock_event = MagicMock()
        mock_event.source.user_id = mock_event.source.group_id = "123"
        mock_event.message.text = "t"
        with self.app.app_context():
            res = match_text_and_assign(mock_event)
        self.assertIsInstance(res, TemplateSendMessage)
        self.assertEqual(res.alt_text, "請選擇查詢交通類型")
        mock_event.message.text = "T"
        with self.app.app_context():
            res = match_text_and_assign(mock_event)
        self.assertIsInstance(res, TemplateSendMessage)
        self.assertEqual(res.alt_text, "請選擇查詢交通類型")

    def test_if_one_TRA_questionstate_exists_and_start_search_THSR(self):
        mock_event = MagicMock()
        mock_event.source.user_id = mock_event.source.group_id = user_id = group_id = "123"
        mock_event.message.text = "查高鐵"
        q_1 = TRA_QuestionState(group=group_id, user=user_id, departure_station="新竹")
        self.app.session.add(q_1)
        with self.app.app_context():
            res = match_text_and_assign(mock_event)
        # Check q_1 has been expired
        rq_1 = self.app.session.query(TRA_QuestionState).one()
        self.assertTrue(rq_1.expired)
        # Check that THSR has been created
        rq_2 = self.app.session.query(THSR_QuestionState).one()
        self.assertFalse(rq_2.expired)
        self.assertEqual(rq_2.user, user_id)
        self.assertEqual(rq_2.group, group_id)
        self.assertEqual(res.text, "請輸入起程站")

    def test_if_multiple_TRA_questionstates_exists_and_start_search_TRA(self):
        mock_event = MagicMock()
        mock_event.source.user_id = mock_event.source.group_id = user_id = group_id = "123"
        mock_event.message.text = "查臺鐵"
        q_1 = TRA_QuestionState(group=group_id, user=user_id, departure_station="新竹")
        q_1.expired = True
        q_2 = TRA_QuestionState(group=group_id, user=user_id, departure_station="高雄")
        self.app.session.add(q_1)
        self.app.session.add(q_2)
        with self.app.app_context():
            res = match_text_and_assign(mock_event)
        rq_1 = self.app.session.query(TRA_QuestionState).filter_by(expired=True).all()
        self.assertEqual(len(rq_1), 2)
        rq_2 = self.app.session.query(TRA_QuestionState).filter_by(expired=False).one()
        self.assertEqual(rq_2.user, user_id)
        self.assertEqual(rq_2.group, group_id)
        self.assertEqual(res.text, "請輸入起程站")

    def test_if_multiple_THSR_questionstates_exists_and_start_search_THSR(self):
        mock_event = MagicMock()
        mock_event.source.user_id = mock_event.source.group_id = user_id = group_id = "123"
        mock_event.message.text = "查高鐵"
        q_1 = THSR_QuestionState(group=group_id, user=user_id, departure_station="新竹")
        q_1.expired = True
        q_2 = THSR_QuestionState(group=group_id, user=user_id, departure_station="左營")
        self.app.session.add(q_1)
        self.app.session.add(q_2)
        with self.app.app_context():
            res = match_text_and_assign(mock_event)
        rq_1 = self.app.session.query(THSR_QuestionState).filter_by(expired=True).all()
        self.assertEqual(len(rq_1), 2)
        rq_2 = self.app.session.query(THSR_QuestionState).filter_by(expired=False).one()
        self.assertEqual(rq_2.user, user_id)
        self.assertEqual(rq_2.group, group_id)
        self.assertEqual(res.text, "請輸入起程站")
