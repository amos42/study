import unittest
from datetime import UTC
from datetime import datetime
from datetime import time
from datetime import timedelta
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch
from uuid import UUID

import pytest

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


def _make_sample_data(notice_id: int = 1, create_at: datetime = None, delay_day: int = 0) -> NoticeDomain:
    now = create_at if create_at else datetime.now(UTC)
    begin_date = datetime.combine(now.date(), time(0, 0, 0), UTC) + timedelta(days=delay_day)
    return NoticeDomain(
        notice_id=notice_id,
        notice_title=f"Sample Notice {notice_id}",
        notice_contents=f"This is a sample notice {notice_id}.",
        begin_date=begin_date,
        end_date=begin_date + timedelta(days=1),
        is_urgent=False,
        is_active=True,
        is_exposure=False,
        creator=UUID(int=notice_id),
        modifier=UUID(int=notice_id),
        created_at=now,
        modified_at=now,
        creator_name=f"tester_{notice_id}",
        modifier_name=f"tester_{notice_id}",
    )


def _make_sample_table_data_list(count: int, create_at: datetime) -> list[NoticeTable]:
    samples = []
    for i in range(1, count + 1):
        record = NoticeTable.from_domain(_make_sample_data(i, create_at, i - count//2))
        samples.append(record)
    return samples


class TestDatabaseNoticeRepository(unittest.TestCase):
    create_at: datetime
    samples: list[NoticeTable]
    current_session_record: NoticeTable = None

    def create_db_mock(self):
        db_mock = Mock()
        db_mock.engine = Mock()
        db_mock.engine.pool = Mock()
        db_mock.engine.pool.status = Mock(return_value="active")
        db_mock.session = Mock(side_effect=lambda: iter([self.mock_session]))
        return db_mock

    def setUp(self):
        self.create_at = datetime.now(UTC)
        self.samples = _make_sample_table_data_list(10, self.create_at)

        self.mock_session = Mock()

        def get_side_effect(tbl, pk):
            return next((s for s in self.samples if s.id == pk), None)

        self.mock_session.get.side_effect = Mock(side_effect=get_side_effect)

        def add_side_effect(tbl):
            self.samples.append(tbl)
            self.current_session_record = tbl

        self.mock_session.add = Mock(side_effect=add_side_effect)
        self.mock_session.commit = Mock()

        def delete_side_effect(tbl):
            self.samples.remove(tbl)

        self.mock_session.delete = Mock(side_effect=delete_side_effect)
        self.mock_session.flush = Mock()

        def refresh_side_effect(tbl):
            tbl.__dict__.update(self.current_session_record.__dict__)

        self.mock_session.refresh = Mock(side_effect=refresh_side_effect)

        def scalars_side_effect(*args, **kwargs):
            scalar = MagicMock()

            def all_side_effect() -> list[NoticeTable]:
                self.samples.sort(key=lambda x: x.created_at, reverse=True)
                return self.samples

            scalar.all = Mock(side_effect=all_side_effect)

            def first_side_effect() -> NoticeTable | None:
                if not self.samples or len(self.samples) == 0:
                    return None
                self.samples.sort(key=lambda x: x.created_at, reverse=True)
                return self.samples[0]

            scalar.first = Mock(side_effect=first_side_effect)

            def one_side_effect() -> NoticeTable:
                if not self.samples or len(self.samples) == 0:
                    raise Exception("No result found")
                self.samples.sort(key=lambda x: x.created_at, reverse=True)
                return self.samples[0]

            scalar.one = Mock(side_effect=one_side_effect)
            return scalar

        self.mock_session.scalars = Mock(side_effect=scalars_side_effect)

        def query_side_effect(*args, **kwargs):
            query = MagicMock()
            query._filtered.return_value = self.samples
            query._offset.return_value = None
            query._limit.return_value = None

            def offset_side_effect(offset_value: int):
                query._offset.return_value = offset_value
                return query

            def limit_side_effect(limit_value: int):
                query._limit.return_value = limit_value
                return query

            def filter_side_effect(*args, **kwargs):
                filtered = query._filtered.return_value
                for condition in args:
                    # if condition.group:
                    if hasattr(condition.left, "name") and condition.left.name == "id":
                        value = condition.right.effective_value
                        filtered = [s for s in filtered if s.id == value]
                    if hasattr(condition.left, "name") and condition.left.name == "notice_contents":
                        value = condition.right.effective_value
                        filtered = [s for s in filtered if s.notice_contents == value]
                    if hasattr(condition.left, "name") and condition.left.name == "modified_at":
                        value = condition.right.effective_value
                        filtered = [s for s in filtered if s.modified_at == value]
                    if hasattr(condition.left, "name") and condition.left.name == "is_active":
                        value = condition.right.effective_value
                        filtered = [s for s in filtered if s.is_active == value]
                    if hasattr(condition.left, "name") and condition.left.name == "begin_date":
                        value = condition.right.effective_value
                        filtered = [s for s in filtered if condition.operator(s.begin_date, value)]
                    if hasattr(condition.left, "name") and condition.left.name == "end_date":
                        value = condition.right.effective_value
                        print(condition.operator.__name__)
                        filtered = [s for s in filtered if condition.operator(s.end_date, value)]
                query._filtered.return_value = filtered
                return query

            def order_by_side_effect(*args, **kwargs):
                # lst = query._filtered()
                # lst.sort(key=lambda x: x.created_at, reverse=True)
                # query._filtered.return_value = lst
                return query

            def first_side_effect() -> NoticeTable | None:
                lst = query._filtered()
                if not lst:
                    return None
                if len(lst) == 0:
                    return None
                return lst[0]

            def all_side_effect() -> list[NoticeTable]:
                offset = query._offset()
                limit = query._limit()
                if not offset or not limit:
                    return query._filtered()
                lst = query._filtered()
                return lst[offset : offset + limit]

            def count_side_effect() -> int:
                cnt = len(query._filtered())
                offset = query._offset()
                limit = query._limit()
                if not offset or not limit:
                    return cnt
                cnt -= offset
                if cnt < 0:
                    return 0
                return min(cnt, limit)

            query.filter = MagicMock(side_effect=filter_side_effect)
            query.offset = Mock(side_effect=offset_side_effect)
            query.limit = Mock(side_effect=limit_side_effect)
            query.order_by = Mock(side_effect=order_by_side_effect)
            query.first = Mock(side_effect=first_side_effect)
            query.all = Mock(side_effect=all_side_effect)
            query.count = Mock(side_effect=count_side_effect)
            return query

        self.mock_session.query = Mock(side_effect=query_side_effect)
        self.repository = DatabaseSystemNoticeRepository()

        db_mock = self.create_db_mock()
        self.db_patch = patch("genai.base.common.database.db", db_mock)
        self.db_patch.start()

    def tearDown(self):
        self.db_patch.stop()

    def test_data_exchange(self):
        notice_data = _make_sample_data()

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
        notice_data = _make_sample_data()

        result: NoticeDomain = self.repository.create(notice_data)

        self.assertIsInstance(result, NoticeDomain)
        self.assertEqual(result.notice_id, 1)
        self.assertEqual(result.notice_title, notice_data.notice_title)
        self.assertEqual(result.notice_contents, notice_data.notice_contents)
        self.assertEqual(result.begin_date, notice_data.begin_date)
        self.assertEqual(result.end_date, notice_data.end_date)
        self.assertEqual(result.is_urgent, notice_data.is_urgent)
        self.assertEqual(result.is_active, notice_data.is_active)
        self.assertEqual(result.is_exposure, notice_data.is_exposure)
        self.assertEqual(result.creator, notice_data.creator)
        # self.assertEqual(result.modified_at.replace(tzinfo=UTC).astimezone(UTC), notice_data.modified_at)

    def test_update(self):
        notice_data = _make_sample_data()

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
        notice_data = _make_sample_data(999)

        # Expect the ServerException to be raised
        with pytest.raises(ServerException) as exc_info:
            self.repository.update(notice_data)

        # Check the exception details
        assert exc_info.value.error_code == "COMMON_ERROR_2"
        assert str(exc_info.value.detail_message) == "The Notice [999] does not exist"

    def test_delete(self):
        result = self.repository.delete(1)
        self.assertIsInstance(result, NoticeDomain)
        self.assertEqual(result.notice_id, 1)

    def test_delete_error(self):
        with pytest.raises(ServerException) as exc_info:
            self.repository.delete(999)

        assert exc_info.value.error_code == "COMMON_ERROR_2"
        assert str(exc_info.value.detail_message) == "The Notice [999] does not exist"

    def test_select_by_id(self):
        notice_data = _make_sample_data(1, self.create_at, -5)

        result: NoticeDomain = self.repository.select_by_id(1)

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
        # self.assertEqual(result.modified_at, notice_data.modified_at)

    def test_select_by_id_error(self):
        with pytest.raises(ServerException) as exc_info:
            self.repository.select_by_id(999)

        assert exc_info.value.error_code == "COMMON_ERROR_4"
        assert str(exc_info.value.detail_message) == "The Notice [999] does not exist"

    def test_get_notice_page_list(self):
        notice_data = _make_sample_data(6, self.create_at, 1)

        pagination = PaginationParams(page=2, limit=5)

        result: Page = self.repository.get_notice_page_list(pagination=pagination)

        self.assertIsInstance(result, Page)
        result_page = result.meta
        self.assertEqual(result_page.totalItems, 10)
        self.assertEqual(result_page.itemCount, 5)
        self.assertEqual(result_page.itemsPerPage, 5)
        self.assertEqual(result_page.currentPage, 2)
        self.assertEqual(result_page.totalPages, 2)
        result_items: list[NoticeDomain] = result.items
        self.assertEqual(len(result_items), 5)
        self.assertIsInstance(result_items[0], NoticeDomain)
        self.assertEqual(result_items[0].notice_id, notice_data.notice_id)
        self.assertEqual(result_items[0].notice_title, notice_data.notice_title)
        self.assertEqual(result_items[0].notice_contents, notice_data.notice_contents)
        self.assertEqual(result_items[0].begin_date, notice_data.begin_date)
        self.assertEqual(result_items[0].end_date, notice_data.end_date)
        self.assertEqual(result_items[0].is_urgent, notice_data.is_urgent)
        self.assertEqual(result_items[0].is_active, notice_data.is_active)
        self.assertEqual(result_items[0].is_exposure, notice_data.is_exposure)
        self.assertEqual(result_items[0].creator, notice_data.creator)
        # self.assertEqual(result_items[0].modified_at, notice_data.modified_at)

    def test_get_notice_page_list_before(self):
        notice_data = _make_sample_data(6, self.create_at, 1)
        # notice_data.begin_date = datetime.now(UTC) + timedelta(hours=1)
        # notice_data.end_date = datetime.now(UTC) + timedelta(hours=2)

        pagination = PaginationParams(page=1, limit=10)

        notice_search_contidtion_paramas = NoticeSearchConditionParams(status=NoticeConditionStatus.BEFORE)
        result = self.repository.get_notice_page_list(condition=notice_search_contidtion_paramas, pagination=pagination)

        self.assertIsInstance(result, Page)
        result_page = result.meta
        self.assertEqual(result_page.totalItems, 5)
        self.assertEqual(result_page.itemCount, 5)
        self.assertEqual(result_page.itemsPerPage, 10)
        self.assertEqual(result_page.currentPage, 1)
        self.assertEqual(result_page.totalPages, 1)
        result_items: list[NoticeDomain] = result.items
        self.assertEqual(len(result_items), 5)
        self.assertIsInstance(result_items[0], NoticeDomain)
        self.assertEqual(result_items[0].notice_id, notice_data.notice_id)
        self.assertEqual(result_items[0].notice_title, notice_data.notice_title)
        self.assertEqual(result_items[0].notice_contents, notice_data.notice_contents)
        self.assertEqual(result_items[0].begin_date, notice_data.begin_date)
        self.assertEqual(result_items[0].end_date, notice_data.end_date)
        self.assertEqual(result_items[0].is_urgent, notice_data.is_urgent)
        self.assertEqual(result_items[0].is_active, notice_data.is_active)
        self.assertEqual(result_items[0].is_exposure, notice_data.is_exposure)
        self.assertEqual(result_items[0].creator, notice_data.creator)
        # self.assertEqual(result_items[0].modified_at, notice_data.modified_at)

    def test_get_notice_page_list_inprogress(self):
        notice_data = _make_sample_data(1)
        now = datetime.now(UTC)
        notice_data.begin_date = now - timedelta(hours=1)
        notice_data.end_date = datetime.combine(now.date(), time(0, 0, 0), UTC) + timedelta(hours=1)

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
        self.assertEqual(len(result_items), 10)
        self.assertIsInstance(result_items[0], NoticeDomain)
        self.assertEqual(result_items[0].notice_id, notice_data.notice_id)
        self.assertEqual(result_items[0].notice_title, notice_data.notice_title)
        self.assertEqual(result_items[0].notice_contents, notice_data.notice_contents)
        self.assertEqual(result_items[0].begin_date, notice_data.begin_date)
        self.assertEqual(result_items[0].end_date, notice_data.end_date)
        self.assertEqual(result_items[0].is_urgent, notice_data.is_urgent)
        self.assertEqual(result_items[0].is_active, notice_data.is_active)
        self.assertEqual(result_items[0].is_exposure, notice_data.is_exposure)
        self.assertEqual(result_items[0].creator, notice_data.creator)
        # self.assertEqual(result_items[0].modified_at, notice_data.modified_at)

    def test_get_notice_page_list_inactive(self):
        notice_data = _make_sample_data(1)
        now = datetime.now(UTC)
        midnight_nowTime = datetime.combine(now.date(), time(0, 0, 0), UTC)
        notice_data.begin_date = midnight_nowTime + timedelta(hours=48)
        notice_data.end_date = midnight_nowTime - timedelta(hours=48)

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
        self.assertEqual(len(result_items), 10)
        self.assertIsInstance(result_items[0], NoticeDomain)
        self.assertEqual(result_items[0].notice_id, notice_data.notice_id)
        self.assertEqual(result_items[0].notice_title, notice_data.notice_title)
        self.assertEqual(result_items[0].notice_contents, notice_data.notice_contents)
        self.assertEqual(result_items[0].begin_date, notice_data.begin_date)
        self.assertEqual(result_items[0].end_date, notice_data.end_date)
        self.assertEqual(result_items[0].is_urgent, notice_data.is_urgent)
        self.assertEqual(result_items[0].is_active, notice_data.is_active)
        self.assertEqual(result_items[0].is_exposure, notice_data.is_exposure)
        self.assertEqual(result_items[0].creator, notice_data.creator)
        # self.assertEqual(result_items[0].modified_at, notice_data.modified_at)

    def test_get_notice_page_list_expired(self):
        notice_data = _make_sample_data(1)
        notice_data.end_date = datetime.combine(datetime.now(UTC).date(), time(0, 0, 0), UTC) - timedelta(hours=1)

        pagination = PaginationParams(page=1, limit=10)

        notice_search_contidtion_paramas = NoticeSearchConditionParams(status=NoticeConditionStatus.EXPIRED)
        result = self.repository.get_notice_page_list(condition=notice_search_contidtion_paramas, pagination=pagination)

        self.assertIsInstance(result, Page)
        result_page = result.meta
        self.assertEqual(result_page.totalItems, 3)
        self.assertEqual(result_page.itemCount, 3)
        self.assertEqual(result_page.itemsPerPage, 10)
        self.assertEqual(result_page.currentPage, 1)
        self.assertEqual(result_page.totalPages, 1)
        result_items: list[NoticeDomain] = result.items
        self.assertEqual(len(result_items), 3)
        self.assertIsInstance(result_items[0], NoticeDomain)
        self.assertEqual(result_items[0].notice_id, notice_data.notice_id)
        self.assertEqual(result_items[0].notice_title, notice_data.notice_title)
        self.assertEqual(result_items[0].notice_contents, notice_data.notice_contents)
        # self.assertEqual(result_items[0].begin_date, notice_data.begin_date)
        # self.assertEqual(result_items[0].end_date, notice_data.end_date)
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

