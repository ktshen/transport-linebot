import unittest
from unittest.mock import patch
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
from models import (
    Base, THSR_TrainTimeTable, THSR_TableEntry, THSR_Train, THSR_BuildingStatusOnDate,
    TRA_TrainTimeTable, TRA_Train, TRA_TableEntry, TRA_BuildingStatusOnDate
)
from build_database import build_THSR_database_by_date, build_TRA_database_by_date
from .load_example import drop_all_table, TimeTableExampleLoader, load_example_timetable_to_database

engine = create_engine(os.environ["TESTING_DATABASE_URI"])
Session = sessionmaker(bind=engine)


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.session = Session()
        Base.metadata.create_all(engine)

    def tearDown(self):
        self.session.close()
        drop_all_table(engine)


class TestCase_for_build_TRA_database_by_date(BaseTestCase):
    @patch("build_database.request_TRA_all_train_timetable_by_date")
    def test_building(self, mock_request):
        # input first day data
        date_input = date(2018, 6, 2)
        loader = TimeTableExampleLoader(date_input)
        timetables = list()
        for tb in loader:
            timetables.append(tb)
        mock_request.return_value = timetables
        resp = build_TRA_database_by_date(date_input, self.session)
        self.assertEqual(resp.value, 0)
        self.assertEqual(self.session.query(TRA_Train).count(), 902)
        self.assertEqual(self.session.query(TRA_TrainTimeTable).count(), 902)
        self.assertEqual(self.session.query(TRA_TableEntry).count(), 18319)
        update_status = self.session.query(TRA_BuildingStatusOnDate).one()
        self.assertEqual(update_status.assigned_date, date_input)
        self.assertEqual(update_status.status, 2)
        # Input second day data
        date_input_2 = date(2018, 6, 6)
        loader = TimeTableExampleLoader(date_input_2)
        timetables = list()
        for tb in loader:
            timetables.append(tb)
        mock_request.return_value = timetables
        resp = build_TRA_database_by_date(date_input_2, self.session)
        self.assertEqual(resp.value, 0)
        self.assertEqual(self.session.query(TRA_Train).count(), 940)
        self.assertEqual(self.session.query(TRA_TrainTimeTable).count(), 1811)
        self.assertEqual(self.session.query(TRA_TableEntry).count(), 36771)
        self.assertEqual(self.session.query(TRA_BuildingStatusOnDate).count(), 2)

        # Build second day data again
        resp = build_TRA_database_by_date(date_input_2, self.session, build_anyway=True)
        self.assertEqual(resp.value, 0)
        self.assertEqual(self.session.query(TRA_Train).count(), 940)
        self.assertEqual(self.session.query(TRA_TrainTimeTable).count(), 1811)
        self.assertEqual(self.session.query(TRA_TableEntry).count(), 36771)
        self.assertEqual(self.session.query(TRA_BuildingStatusOnDate).count(), 2)

    @patch("build_database.request_TRA_all_train_timetable_by_date")
    def test_remove_old_data_before_building(self, mock_request_train_no):
        date_input = date(2018, 6, 2)
        load_example_timetable_to_database(self.session, date_input)
        self.assertEqual(self.session.query(TRA_Train).count(), 902)
        self.assertEqual(self.session.query(TRA_TrainTimeTable).count(), 902)
        self.assertEqual(self.session.query(TRA_TableEntry).count(), 18319)
        build_status = self.session.query(TRA_BuildingStatusOnDate).one()
        self.assertEqual(build_status.status, 2)

        mock_request_train_no.return_value = []
        resp = build_TRA_database_by_date(date_input, self.session, build_anyway=True)
        self.assertEqual(resp.value, 0)
        self.assertEqual(self.session.query(TRA_Train).count(), 902)
        self.assertEqual(self.session.query(TRA_TrainTimeTable).count(), 0)
        self.assertEqual(self.session.query(TRA_TableEntry).count(), 0)
        build_status = self.session.query(TRA_BuildingStatusOnDate).one()
        self.assertEqual(build_status.status, 3)

    def test_if_already_built_then_skip(self):
        date_input = date(2018, 6, 2)
        status = TRA_BuildingStatusOnDate(date_input, status=2)
        self.session.add(status)
        resp = build_TRA_database_by_date(date_input, self.session)
        self.assertEqual(resp.value, 0)
        self.assertEqual(self.session.query(TRA_Train).count(), 0)
        self.assertEqual(self.session.query(TRA_TrainTimeTable).count(), 0)
        self.assertEqual(self.session.query(TRA_TableEntry).count(), 0)


class TestCase_for_build_THSR_database_by_date(BaseTestCase):
    @patch("build_database.request_THSR_all_train_timetable")
    def test_building(self, mock_request):
        # input first day data
        date_input = date(2018, 6, 5)
        loader = TimeTableExampleLoader(date_input, "THSR")
        response = list()
        for tb in loader:
            response.append(tb)
        mock_request.return_value = response
        resp = build_THSR_database_by_date(date_input, self.session)
        self.assertEqual(resp.value, 0)
        self.assertEqual(self.session.query(THSR_Train).count(), 128)
        self.assertEqual(self.session.query(THSR_TrainTimeTable).count(), 128)
        self.assertEqual(self.session.query(THSR_TableEntry).count(), 1085)
        self.assertEqual(self.session.query(THSR_BuildingStatusOnDate).count(), 1)
        update_status = self.session.query(THSR_BuildingStatusOnDate).one()
        self.assertEqual(update_status.assigned_date, date_input)
        self.assertEqual(update_status.status, 2)
        # Input second day data
        date_input_2 = date(2018, 6, 9)
        loader = TimeTableExampleLoader(date_input_2, "THSR")
        response = list()
        for tb in loader:
            response.append(tb)
        mock_request.return_value = response
        resp = build_THSR_database_by_date(date_input_2, self.session)
        self.assertEqual(resp.value, 0)
        self.assertEqual(self.session.query(THSR_Train).count(), 150)
        self.assertEqual(self.session.query(THSR_TrainTimeTable).count(), 272)
        self.assertEqual(self.session.query(THSR_TableEntry).count(), 2301)
        self.assertEqual(self.session.query(THSR_BuildingStatusOnDate).count(), 2)

        # Build second day data again
        resp = build_THSR_database_by_date(date_input_2, self.session, build_anyway=True)
        self.assertEqual(resp.value, 0)
        self.assertEqual(self.session.query(THSR_Train).count(), 150)
        self.assertEqual(self.session.query(THSR_TrainTimeTable).count(), 272)
        self.assertEqual(self.session.query(THSR_TableEntry).count(), 2301)
        self.assertEqual(self.session.query(THSR_BuildingStatusOnDate).count(), 2)

        # Build first day data again
        loader = TimeTableExampleLoader(date_input, "THSR")
        response = list()
        for tb in loader:
            response.append(tb)
        mock_request.return_value = response
        resp = build_THSR_database_by_date(date_input, self.session, build_anyway=True)
        self.assertEqual(resp.value, 0)
        self.assertEqual(self.session.query(THSR_Train).count(), 150)
        self.assertEqual(self.session.query(THSR_TrainTimeTable).count(), 272)
        self.assertEqual(self.session.query(THSR_TableEntry).count(), 2301)
        self.assertEqual(self.session.query(THSR_BuildingStatusOnDate).count(), 2)
        self.assertEqual(self.session.query(THSR_BuildingStatusOnDate).count(), 2)

    @patch("build_database.request_THSR_all_train_timetable")
    def test_remove_old_data_before_building(self, mock_request):
        date_input = date(2018, 6, 5)
        load_example_timetable_to_database(self.session, date_input, "THSR")
        self.assertEqual(self.session.query(THSR_Train).count(), 128)
        self.assertEqual(self.session.query(THSR_TrainTimeTable).count(), 128)
        self.assertEqual(self.session.query(THSR_TableEntry).count(), 1085)
        build_status = self.session.query(THSR_BuildingStatusOnDate).one()
        self.assertEqual(build_status.status, 2)

        mock_request.return_value = []
        resp = build_THSR_database_by_date(date_input, self.session, build_anyway=True)
        self.assertEqual(resp.value, 0)
        self.assertEqual(self.session.query(THSR_Train).count(), 128)
        self.assertEqual(self.session.query(THSR_TrainTimeTable).count(), 0)
        self.assertEqual(self.session.query(THSR_TableEntry).count(), 0)
        build_status = self.session.query(THSR_BuildingStatusOnDate).one()
        self.assertEqual(build_status.status, 3)

    def test_if_already_built_then_skip(self):
        date_input = date(2018, 6, 2)
        status = THSR_BuildingStatusOnDate(date_input, status=2)
        self.session.add(status)
        resp = build_THSR_database_by_date(date_input, self.session)
        self.assertEqual(resp.value, 0)
        self.assertEqual(self.session.query(THSR_Train).count(), 0)
        self.assertEqual(self.session.query(THSR_TrainTimeTable).count(), 0)
        self.assertEqual(self.session.query(THSR_TableEntry).count(), 0)
