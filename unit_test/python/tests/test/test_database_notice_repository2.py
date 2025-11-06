import unittest
from datetime import UTC
from datetime import datetime
from datetime import time
from datetime import timedelta
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from genai.base.common.database import db
from genai.base.common.exception import ServerException
from genai.base.common.pagination import Page
from genai.base.common.pagination import PaginationParams
from genai.system_admin.adapter.outbound.persistence.database_system_notice_repository import (
    DatabaseSystemNoticeRepository,
)
from genai.system_admin.adapter.outbound.persistence.table.notice_table import NoticeTable
from genai.system_admin.application.condition import NoticeConditionStatus
from genai.system_admin.application.condition import NoticeSearchConditionParams
from genai.system_admin.domain.notice_domain import NoticeDomain


class TestDatabaseNoticeRepository(unittest.TestCase):
    sample_data = NoticeDomain(
        notice_id=1,
        notice_title="Sample Notice",
        notice_contents="This is a sample notice.",
        # begin_date = datetime.now(UTC) - timedelta(days=1),
        # end_date = datetime.now(UTC) + timedelta(days=7),
        is_urgent=False,
        is_active=True,
        is_exposure=False,
        creator=UUID(int=0),
        creator_name="John",
        # created_at = datetime.now(UTC),
        # modified_at = datetime.now(UTC),
    )

    def setUp(self):
        self.repository = DatabaseSystemNoticeRepository()
        try:
            db.init_app(
                app=None,
                database_url="sqlite:///:memory:",
                # database_url="duckdb:///:memory:",
                connect_args={
                    # "check_same_thread": False,
                },
            )
            db.create_table(checkfirst=False)
        except Exception as e:
            print(e)

    def tearDown(self):
        db.shutdown()
        return super().tearDown()

    def get_sample_data(self):
        now = datetime.now(UTC)
        self.sample_data.begin_date = datetime.combine(now.date(), time(0, 0, 0), UTC) - timedelta(hours=1)
        self.sample_data.end_date = self.sample_data.begin_date + timedelta(days=7)
        self.sample_data.created_at = now
        self.sample_data.modified_at = now
        return self.sample_data

    def write_one_record(self, data: NoticeDomain):
        session: Session = next(db.session())
        session.add(NoticeTable.from_domain(data))
        session.commit()

    def test_data_exchange(self):
        notice_data = self.get_sample_data()

        notice_table: NoticeTable = NoticeTable.from_domain(notice_data)

        self.assertIsInstance(notice_table, NoticeTable)
        self.assertEqual(notice_table.id, notice_data.notice_id)
        self.assertEqual(notice_table.notice_title, notice_data.notice_title)
        self.assertEqual(notice_table.notice_contents, notice_data.notice_contents)
        self.assertEqual(notice_table.begin_date, notice_data.begin_date)
        self.assertEqual(notice_table.end_date, notice_data.end_date)
        self.assertEqual(notice_table.is_urgent, notice_data.is_urgent)
        self.assertEqual(notice_table.is_active, notice_data.is_active)
        self.assertEqual(notice_table.is_exposure, notice_data.is_exposure)
        self.assertEqual(notice_table.creator, notice_data.creator)
        self.assertEqual(notice_table.modified_at, notice_data.modified_at)

        notice_data = notice_table.to_domain()

        self.assertEqual(notice_table.id, notice_data.notice_id)
        self.assertEqual(notice_table.notice_title, notice_data.notice_title)
        self.assertEqual(notice_table.notice_contents, notice_data.notice_contents)
        self.assertEqual(notice_table.begin_date, notice_data.begin_date)
        self.assertEqual(notice_table.end_date, notice_data.end_date)
        self.assertEqual(notice_table.is_urgent, notice_data.is_urgent)
        self.assertEqual(notice_table.is_active, notice_data.is_active)
        self.assertEqual(notice_table.is_exposure, notice_data.is_exposure)
        self.assertEqual(notice_table.creator, notice_data.creator)
        self.assertEqual(notice_table.modified_at, notice_data.modified_at)

    def test_create(self):
        notice_data = self.get_sample_data()

        result: NoticeDomain = self.repository.create(notice_data)

        self.assertIsInstance(result, NoticeDomain)
        self.assertEqual(result.notice_id, 1)
        self.assertEqual(result.notice_title, notice_data.notice_title)
        self.assertEqual(result.notice_contents, notice_data.notice_contents)
        self.assertEqual(result.begin_date.replace(tzinfo=UTC).astimezone(UTC), notice_data.begin_date)
        self.assertEqual(result.end_date.replace(tzinfo=UTC).astimezone(UTC), notice_data.end_date)
        self.assertEqual(result.is_urgent, notice_data.is_urgent)
        self.assertEqual(result.is_active, notice_data.is_active)
        self.assertEqual(result.is_exposure, notice_data.is_exposure)
        self.assertEqual(result.creator, notice_data.creator)
        self.assertEqual(result.modified_at.replace(tzinfo=UTC).astimezone(UTC), notice_data.modified_at)

    def test_update(self):
        notice_data = self.get_sample_data()

        self.write_one_record(notice_data)

        notice_data.notice_title = "Updated Sample Notice"
        notice_data.notice_contents = "This is an updated sample notice."
        notice_data.modifier = UUID(int=2)
        notice_data.modified_at = datetime.now(UTC)

        result: NoticeDomain = self.repository.update(notice_data)

        self.assertIsInstance(result, NoticeDomain)
        self.assertEqual(result.notice_id, notice_data.notice_id)
        self.assertEqual(result.notice_title, notice_data.notice_title)
        self.assertEqual(result.notice_contents, notice_data.notice_contents)
        self.assertEqual(result.begin_date, notice_data.begin_date)
        self.assertEqual(result.end_date, notice_data.end_date)
        self.assertEqual(result.is_urgent, notice_data.is_urgent)
        self.assertEqual(result.is_active, notice_data.is_active)
        self.assertEqual(result.is_exposure, notice_data.is_exposure)
        self.assertEqual(result.creator, notice_data.creator)
        self.assertEqual(result.modified_at, notice_data.modified_at)

    def test_update_error(self):
        notice_data = self.get_sample_data().model_copy(deep=True)

        notice_data.notice_title = "Updated Sample Notice"
        notice_data.notice_contents = "This is an updated sample notice."
        notice_data.modifier = UUID(int=2)
        notice_data.modified_at = datetime.now(UTC)

        # Expect the ServerException to be raised
        with pytest.raises(ServerException) as exc_info:
            self.repository.update(notice_data)

        # Check the exception details
        assert exc_info.value.error_code == "COMMON_ERROR_2"
        assert str(exc_info.value.detail_message) == "The Notice [1] does not exist"

    def test_delete(self):
        self.write_one_record(self.get_sample_data())

        notice_data = self.get_sample_data()

        result = self.repository.delete(1)
        self.assertIsInstance(result, NoticeDomain)
        self.assertEqual(result.notice_id, notice_data.notice_id)

    def test_delete_error(self):
        with pytest.raises(ServerException) as exc_info:
            self.repository.delete(1)

        assert exc_info.value.error_code == "COMMON_ERROR_2"
        assert str(exc_info.value.detail_message) == "The Notice [1] does not exist"

    def test_select_list(self):
        self.write_one_record(self.get_sample_data())

        notice_data = self.get_sample_data()

        result: list[NoticeDomain] = self.repository.select_list()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], NoticeDomain)
        self.assertEqual(result[0].notice_id, notice_data.notice_id)
        self.assertEqual(result[0].notice_title, notice_data.notice_title)
        self.assertEqual(result[0].notice_contents, notice_data.notice_contents)
        self.assertEqual(result[0].begin_date.replace(tzinfo=UTC).astimezone(UTC), notice_data.begin_date)
        self.assertEqual(result[0].end_date.replace(tzinfo=UTC).astimezone(UTC), notice_data.end_date)
        # self.assertEqual(result[0].created_at.replace(tzinfo=UTC).astimezone(UTC), notice_data.created_at)
        # self.assertEqual(result[0].modified_at.replace(tzinfo=UTC).astimezone(UTC), notice_data.modified_at)

    def test_select_by_id(self):
        self.write_one_record(self.get_sample_data())

        notice_data = self.get_sample_data()

        result: NoticeDomain = self.repository.select_by_id(1)

        self.assertIsInstance(result, NoticeDomain)
        self.assertEqual(result.notice_id, notice_data.notice_id)
        self.assertEqual(result.notice_title, notice_data.notice_title)
        self.assertEqual(result.notice_contents, notice_data.notice_contents)
        self.assertEqual(result.begin_date.replace(tzinfo=UTC).astimezone(UTC), notice_data.begin_date)
        self.assertEqual(result.end_date.replace(tzinfo=UTC).astimezone(UTC), notice_data.end_date)
        self.assertEqual(result.is_urgent, notice_data.is_urgent)
        self.assertEqual(result.is_active, notice_data.is_active)
        self.assertEqual(result.is_exposure, notice_data.is_exposure)
        self.assertEqual(result.creator, notice_data.creator)
        # self.assertEqual(result.modified_at, notice_data.modified_at)

    def test_select_by_id_error(self):
        with pytest.raises(ServerException) as exc_info:
            self.repository.select_by_id(1)

        assert exc_info.value.error_code == "COMMON_ERROR_4"
        assert str(exc_info.value.detail_message) == "The Notice [1] does not exist"

    def test_get_notice_page_list(self):
        self.write_one_record(self.get_sample_data())

        notice_data = self.get_sample_data()

        pagination = PaginationParams(page=1, limit=10)

        result: Page = self.repository.get_notice_page_list(pagination=pagination)

        self.assertIsInstance(result, Page)
        result_page = result.meta
        self.assertEqual(result_page.totalItems, 1)
        self.assertEqual(result_page.itemCount, 1)
        self.assertEqual(result_page.itemsPerPage, 10)
        self.assertEqual(result_page.currentPage, 1)
        self.assertEqual(result_page.totalPages, 1)
        result_items: list[NoticeDomain] = result.items
        self.assertEqual(len(result_items), 1)
        self.assertIsInstance(result_items[0], NoticeDomain)
        self.assertEqual(result_items[0].notice_id, notice_data.notice_id)
        self.assertEqual(result_items[0].notice_title, notice_data.notice_title)
        self.assertEqual(result_items[0].notice_contents, notice_data.notice_contents)
        self.assertEqual(result_items[0].begin_date.replace(tzinfo=UTC).astimezone(UTC), notice_data.begin_date)
        self.assertEqual(result_items[0].end_date.replace(tzinfo=UTC).astimezone(UTC), notice_data.end_date)
        self.assertEqual(result_items[0].is_urgent, notice_data.is_urgent)
        self.assertEqual(result_items[0].is_active, notice_data.is_active)
        self.assertEqual(result_items[0].is_exposure, notice_data.is_exposure)
        self.assertEqual(result_items[0].creator, notice_data.creator)
        # self.assertEqual(result_items[0].modified_at, notice_data.modified_at)

    def test_get_notice_page_list_before(self):
        notice_data = self.get_sample_data().model_copy()
        notice_data.begin_date = datetime.now(UTC) + timedelta(hours=1)
        notice_data.end_date = datetime.now(UTC) + timedelta(hours=2)
        self.write_one_record(notice_data)

        pagination = PaginationParams(page=1, limit=10)

        notice_search_contidtion_paramas = NoticeSearchConditionParams(status=NoticeConditionStatus.BEFORE)
        result = self.repository.get_notice_page_list(condition=notice_search_contidtion_paramas, pagination=pagination)

        self.assertIsInstance(result, Page)
        result_page = result.meta
        self.assertEqual(result_page.totalItems, 1)
        self.assertEqual(result_page.itemCount, 1)
        self.assertEqual(result_page.itemsPerPage, 10)
        self.assertEqual(result_page.currentPage, 1)
        self.assertEqual(result_page.totalPages, 1)
        result_items: list[NoticeDomain] = result.items
        self.assertEqual(len(result_items), 1)
        self.assertIsInstance(result_items[0], NoticeDomain)
        self.assertEqual(result_items[0].notice_id, notice_data.notice_id)
        self.assertEqual(result_items[0].notice_title, notice_data.notice_title)
        self.assertEqual(result_items[0].notice_contents, notice_data.notice_contents)
        self.assertEqual(result_items[0].begin_date.replace(tzinfo=UTC).astimezone(UTC), notice_data.begin_date)
        self.assertEqual(result_items[0].end_date.replace(tzinfo=UTC).astimezone(UTC), notice_data.end_date)
        self.assertEqual(result_items[0].is_urgent, notice_data.is_urgent)
        self.assertEqual(result_items[0].is_active, notice_data.is_active)
        self.assertEqual(result_items[0].is_exposure, notice_data.is_exposure)
        self.assertEqual(result_items[0].creator, notice_data.creator)
        # self.assertEqual(result_items[0].modified_at, notice_data.modified_at)

    def test_get_notice_page_list_inprogress(self):
        notice_data = self.get_sample_data().model_copy()
        now = datetime.now(UTC)
        notice_data.begin_date = now - timedelta(hours=1)
        notice_data.end_date = datetime.combine(now.date(), time(0, 0, 0), UTC) + timedelta(hours=1)
        self.write_one_record(notice_data)

        pagination = PaginationParams(page=1, limit=10)

        notice_search_contidtion_paramas = NoticeSearchConditionParams(status=NoticeConditionStatus.INPROGRESS)
        result = self.repository.get_notice_page_list(condition=notice_search_contidtion_paramas, pagination=pagination)

        self.assertIsInstance(result, Page)
        result_page = result.meta
        self.assertEqual(result_page.totalItems, 1)
        self.assertEqual(result_page.itemCount, 1)
        self.assertEqual(result_page.itemsPerPage, 10)
        self.assertEqual(result_page.currentPage, 1)
        self.assertEqual(result_page.totalPages, 1)
        result_items: list[NoticeDomain] = result.items
        self.assertEqual(len(result_items), 1)
        self.assertIsInstance(result_items[0], NoticeDomain)
        self.assertEqual(result_items[0].notice_id, notice_data.notice_id)
        self.assertEqual(result_items[0].notice_title, notice_data.notice_title)
        self.assertEqual(result_items[0].notice_contents, notice_data.notice_contents)
        self.assertEqual(result_items[0].begin_date.replace(tzinfo=UTC).astimezone(UTC), notice_data.begin_date)
        self.assertEqual(result_items[0].end_date.replace(tzinfo=UTC).astimezone(UTC), notice_data.end_date)
        self.assertEqual(result_items[0].is_urgent, notice_data.is_urgent)
        self.assertEqual(result_items[0].is_active, notice_data.is_active)
        self.assertEqual(result_items[0].is_exposure, notice_data.is_exposure)
        self.assertEqual(result_items[0].creator, notice_data.creator)
        # self.assertEqual(result_items[0].modified_at.replace(tzinfo=UTC).astimezone(UTC), notice_data.modified_at)

    def test_get_notice_page_list_inactive(self):
        notice_data = self.get_sample_data().model_copy()
        now = datetime.now(UTC)
        midnight_nowTime = datetime.combine(now.date(), time(0, 0, 0), UTC)
        notice_data.begin_date = midnight_nowTime + timedelta(hours=48)
        notice_data.end_date = midnight_nowTime - timedelta(hours=48)
        self.write_one_record(notice_data)

        pagination = PaginationParams(page=1, limit=10)

        notice_search_contidtion_paramas = NoticeSearchConditionParams(status=NoticeConditionStatus.INACTIVE)
        result = self.repository.get_notice_page_list(condition=notice_search_contidtion_paramas, pagination=pagination)

        self.assertIsInstance(result, Page)
        result_page = result.meta
        self.assertEqual(result_page.totalItems, 1)
        self.assertEqual(result_page.itemCount, 1)
        self.assertEqual(result_page.itemsPerPage, 10)
        self.assertEqual(result_page.currentPage, 1)
        self.assertEqual(result_page.totalPages, 1)
        result_items: list[NoticeDomain] = result.items
        self.assertEqual(len(result_items), 1)
        self.assertIsInstance(result_items[0], NoticeDomain)
        self.assertEqual(result_items[0].notice_id, notice_data.notice_id)
        self.assertEqual(result_items[0].notice_title, notice_data.notice_title)
        self.assertEqual(result_items[0].notice_contents, notice_data.notice_contents)
        self.assertEqual(result_items[0].begin_date.replace(tzinfo=UTC).astimezone(UTC), notice_data.begin_date)
        self.assertEqual(result_items[0].end_date.replace(tzinfo=UTC).astimezone(UTC), notice_data.end_date)
        self.assertEqual(result_items[0].is_urgent, notice_data.is_urgent)
        self.assertEqual(result_items[0].is_active, notice_data.is_active)
        self.assertEqual(result_items[0].is_exposure, notice_data.is_exposure)
        self.assertEqual(result_items[0].creator, notice_data.creator)
        # self.assertEqual(result_items[0].modified_at.replace(tzinfo=UTC).astimezone(UTC), notice_data.modified_at)

    def test_get_notice_page_list_expired(self):
        notice_data = self.get_sample_data().model_copy()
        notice_data.end_date = datetime.combine(datetime.now(UTC).date(), time(0, 0, 0), UTC) - timedelta(hours=1)
        self.write_one_record(notice_data)

        pagination = PaginationParams(page=1, limit=10)

        notice_search_contidtion_paramas = NoticeSearchConditionParams(status=NoticeConditionStatus.EXPIRED)
        result = self.repository.get_notice_page_list(condition=notice_search_contidtion_paramas, pagination=pagination)

        self.assertIsInstance(result, Page)
        result_page = result.meta
        self.assertEqual(result_page.totalItems, 1)
        self.assertEqual(result_page.itemCount, 1)
        self.assertEqual(result_page.itemsPerPage, 10)
        self.assertEqual(result_page.currentPage, 1)
        self.assertEqual(result_page.totalPages, 1)
        result_items: list[NoticeDomain] = result.items
        self.assertEqual(len(result_items), 1)
        self.assertIsInstance(result_items[0], NoticeDomain)
        self.assertEqual(result_items[0].notice_id, notice_data.notice_id)
        self.assertEqual(result_items[0].notice_title, notice_data.notice_title)
        self.assertEqual(result_items[0].notice_contents, notice_data.notice_contents)
        self.assertEqual(result_items[0].begin_date.replace(tzinfo=UTC).astimezone(UTC), notice_data.begin_date)
        self.assertEqual(result_items[0].end_date.replace(tzinfo=UTC).astimezone(UTC), notice_data.end_date)
        self.assertEqual(result_items[0].is_urgent, notice_data.is_urgent)
        self.assertEqual(result_items[0].is_active, notice_data.is_active)
        self.assertEqual(result_items[0].is_exposure, notice_data.is_exposure)
        self.assertEqual(result_items[0].creator, notice_data.creator)
        # self.assertEqual(result_items[0].modified_at, notice_data.modified_at)

    def test_get_notice_page_list_error(self):
        pagination = PaginationParams(page=1, limit=10)

        notice_search_contidtion_paramas = NoticeSearchConditionParams(status=NoticeConditionStatus.ERROR)
        with pytest.raises(ServerException) as exc_info:
            self.repository.get_notice_page_list(condition=notice_search_contidtion_paramas, pagination=pagination)

        assert exc_info.value.error_code == "COMMON_ERROR_4"
        assert str(exc_info.value.detail_message) == "The Notice Status [ERROR] does not exist"


if __name__ == "__main__":
    # for vanilla unittest
    # unittest.main()
    # for all tests with pytest
    pytest.main(["-s", "-v", __file__])
    # for a specific pytest function
    # pytest.main(["-s", "-v", __file__ + "::test_specific"])
