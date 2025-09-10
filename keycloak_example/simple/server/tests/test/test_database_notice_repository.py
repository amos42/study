import unittest
from datetime import datetime
from datetime import timedelta
from unittest.mock import Mock
from unittest.mock import patch
from uuid import UUID

import pytest

from genai.base.common.exception import ServerException
from genai.base.common.pagination import Page
from genai.base.common.pagination import PaginationParams
from genai.system_admin.adapter.outbound.persistence.database_notice_repository import DatabaseNoticeRepository
from genai.system_admin.application.condition import NoticeConditionStatus
from genai.system_admin.application.condition import NoticeSearchConditionParams
from genai.system_admin.domain.notice_domain import NoticeDomain


class TestDatabaseNoticeRepository(unittest.TestCase):
    def setUp(self):
        self.session_mock = Mock()
        self.repository = DatabaseNoticeRepository()

    @pytest.mark.skip
    def create_db_mock(self):
        db_mock = Mock()
        db_mock.engine = Mock()
        db_mock.engine.pool = Mock()
        db_mock.engine.pool.status = Mock(return_value='active')
        db_mock.session = Mock(side_effect=lambda: iter([self.session_mock]))
        return db_mock

    @pytest.mark.skip
    def create_notice_table_mock(self):
        now = datetime.now()
        notice_table_mock = Mock()
        notice_table_mock.id = 1
        notice_table_mock.notice_title = "Sample Notice"
        notice_table_mock.notice_contents = "This is a sample notice."
        notice_table_mock.begin_date = now - timedelta(days=1)
        notice_table_mock.end_date = now + timedelta(days=7)
        notice_table_mock.is_urgent = False
        notice_table_mock.is_active = True
        notice_table_mock.is_exposure = False
        notice_table_mock.creator = UUID(int=0)
        notice_table_mock.created_at = now
        notice_table_mock.modified_at = now
        notice_table_mock.tenant_id = 1

        def to_domain_side_effect(*args, **kwargs):
            return NoticeDomain(
                notice_id=notice_table_mock.id,
                notice_title=notice_table_mock.notice_title,
                notice_contents=notice_table_mock.notice_contents,
                begin_date=notice_table_mock.begin_date,
                end_date=notice_table_mock.end_date,
                is_urgent=notice_table_mock.is_urgent,
                is_active=notice_table_mock.is_active,
                is_exposure=notice_table_mock.is_exposure,
                creator=notice_table_mock.creator,
                created_at=notice_table_mock.created_at,
                modifier=UUID(int=0),
                modified_at=notice_table_mock.modified_at,
                tenant_id=notice_table_mock.tenant_id
            )

        notice_table_mock.to_domain.side_effect = to_domain_side_effect
        return notice_table_mock

    def test_create(self):
        db_mock = self.create_db_mock()
        notice_table_mock = self.create_notice_table_mock()

        with patch('genai.base.common.database.inject_transactional_session'), \
            patch('genai.base.common.database.db', db_mock), \
            patch('genai.system_admin.adapter.outbound.persistence.table.notice_table.NoticeTable.from_domain',
                  return_value=notice_table_mock):

            result = self.repository.create(notice_table_mock)
            self.assertIsInstance(result, NoticeDomain)
            self.assertEqual(result.notice_id, notice_table_mock.id)
            self.assertEqual(result.notice_title, notice_table_mock.notice_title)
            self.assertEqual(result.notice_contents, notice_table_mock.notice_contents)
            self.assertEqual(result.begin_date, notice_table_mock.begin_date)
            self.assertEqual(result.end_date, notice_table_mock.end_date)
            self.assertEqual(result.is_urgent, notice_table_mock.is_urgent)
            self.assertEqual(result.is_active, notice_table_mock.is_active)
            self.assertEqual(result.is_exposure, notice_table_mock.is_exposure)
            self.assertEqual(result.creator, notice_table_mock.creator)
            self.assertEqual(result.modified_at, notice_table_mock.modified_at)
            self.assertEqual(result.tenant_id, notice_table_mock.tenant_id)

    def test_update(self):
        db_mock = self.create_db_mock()
        notice_table_mock = self.create_notice_table_mock()

        with patch('genai.base.common.database.inject_transactional_session'), \
            patch('genai.base.common.database.db', db_mock), \
            patch('genai.system_admin.adapter.outbound.persistence.table.notice_table.NoticeTable.from_domain',
                  return_value=notice_table_mock):
            self.session_mock.query.return_value.get.return_value = notice_table_mock

            notice_domain = NoticeDomain(
                notice_id=1,
                notice_title="Updated Sample Notice",
                notice_contents="This is an updated sample notice.",
                begin_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now() + timedelta(days=7),
                is_urgent=False,
                is_active=True,
                is_exposure=False,
                creator=notice_table_mock.creator,
                created_at=notice_table_mock.created_at,
                modifier=UUID(int=0),
                modified_at=datetime.now(),
                tenant_id=1
            )

            result = self.repository.update(notice_domain)
            self.assertIsInstance(result, NoticeDomain)
            self.assertEqual(result.notice_id, notice_domain.notice_id)
            self.assertEqual(result.notice_title, notice_domain.notice_title)
            self.assertEqual(result.notice_contents, notice_domain.notice_contents)
            self.assertEqual(result.begin_date, notice_domain.begin_date)
            self.assertEqual(result.end_date, notice_domain.end_date)
            self.assertEqual(result.is_urgent, notice_domain.is_urgent)
            self.assertEqual(result.is_active, notice_domain.is_active)
            self.assertEqual(result.is_exposure, notice_domain.is_exposure)
            self.assertEqual(result.creator, notice_domain.creator)
            self.assertEqual(result.modified_at, notice_domain.modified_at)
            self.assertEqual(result.tenant_id, notice_domain.tenant_id)

    def test_update_error(self):
        db_mock = self.create_db_mock()
        notice_table_mock = self.create_notice_table_mock()

        with patch('genai.base.common.database.inject_transactional_session'), \
            patch('genai.base.common.database.db', db_mock), \
            patch('genai.system_admin.adapter.outbound.persistence.table.notice_table.NoticeTable.from_domain',
                  return_value=notice_table_mock):
            # Set up the mock to return None when querying for the notice
            self.session_mock.query.return_value.get.return_value = None

            notice_domain = NoticeDomain(
                notice_id=1,
                notice_title="Updated Sample Notice",
                notice_contents="This is an updated sample notice.",
                begin_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now() + timedelta(days=7),
                is_urgent=False,
                is_active=True,
                is_exposure=False,
                creator=notice_table_mock.creator,
                created_at=notice_table_mock.created_at,
                modifier=UUID(int=0),
                modified_at=datetime.now(),
                tenant_id=1
            )

            # Expect the ServerException to be raised
            with pytest.raises(ServerException) as exc_info:
                self.repository.update(notice_domain)

            # Check the exception details
            assert exc_info.value.error_code == 'COMMON_ERROR_2'
            assert str(exc_info.value.detail_message) == "The Notice [1] does not exist"

    def test_delete(self):
        db_mock = self.create_db_mock()
        notice_table_mock = self.create_notice_table_mock()

        self.session_mock.query.return_value.get.return_value = notice_table_mock

        with patch('genai.base.common.database.inject_transactional_session'), \
            patch('genai.base.common.database.db', db_mock), \
            patch('genai.system_admin.adapter.outbound.persistence.table.notice_table.NoticeTable.from_domain',
                  return_value=notice_table_mock):
            result = self.repository.delete(1, 1)
            self.assertIsInstance(result, NoticeDomain)
            self.assertEqual(result.notice_id, notice_table_mock.id)
            self.assertEqual(result.notice_title, notice_table_mock.notice_title)
            self.assertEqual(result.notice_contents, notice_table_mock.notice_contents)
            self.assertEqual(result.begin_date, notice_table_mock.begin_date)
            self.assertEqual(result.end_date, notice_table_mock.end_date)
            self.assertEqual(result.is_urgent, notice_table_mock.is_urgent)
            self.assertEqual(result.is_active, notice_table_mock.is_active)
            self.assertEqual(result.is_exposure, notice_table_mock.is_exposure)
            self.assertEqual(result.creator, notice_table_mock.creator)
            self.assertEqual(result.modified_at, notice_table_mock.modified_at)
            self.assertEqual(result.tenant_id, notice_table_mock.tenant_id)

    def test_delete_error(self):
        db_mock = self.create_db_mock()
        notice_table_mock = self.create_notice_table_mock()

        self.session_mock.query.return_value.get.return_value = []

        with patch('genai.base.common.database.inject_transactional_session'), \
            patch('genai.base.common.database.db', db_mock), \
            patch('genai.system_admin.adapter.outbound.persistence.table.notice_table.NoticeTable.from_domain',
                  return_value=notice_table_mock):
            with pytest.raises(ServerException) as exc_info:
                result = self.repository.delete(1, 1)

            assert exc_info.value.error_code == 'COMMON_ERROR_2'
            assert str(exc_info.value.detail_message) == "The Notice [1] does not exist"

    def test_select_list(self):
        db_mock = self.create_db_mock()
        notice_table_mock = self.create_notice_table_mock()

        self.session_mock.query.return_value.all.return_value = [notice_table_mock]

        with patch('genai.base.common.database.inject_transactional_session'), \
            patch('genai.base.common.database.db', db_mock), \
            patch('genai.system_admin.adapter.outbound.persistence.table.notice_table.NoticeTable.from_domain',
                  return_value=notice_table_mock):
            result = self.repository.select_list()
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            self.assertIsInstance(result[0], NoticeDomain)
            self.assertEqual(result[0].notice_id, notice_table_mock.id)
            self.assertEqual(result[0].notice_title, notice_table_mock.notice_title)
            self.assertEqual(result[0].notice_contents, notice_table_mock.notice_contents)
            self.assertEqual(result[0].begin_date, notice_table_mock.begin_date)
            self.assertEqual(result[0].end_date, notice_table_mock.end_date)
            self.assertEqual(result[0].created_at, notice_table_mock.created_at)
            self.assertEqual(result[0].modified_at, notice_table_mock.modified_at)

    def test_select_by_id(self):
        db_mock = self.create_db_mock()
        notice_table_mock = self.create_notice_table_mock()

        self.session_mock.query.return_value.get.return_value = notice_table_mock

        with patch('genai.base.common.database.inject_transactional_session'), \
            patch('genai.base.common.database.db', db_mock), \
            patch('genai.system_admin.adapter.outbound.persistence.table.notice_table.NoticeTable.from_domain',
                  return_value=notice_table_mock):
            result = self.repository.select_by_id(1, 1)
            self.assertIsInstance(result, NoticeDomain)
            self.assertEqual(result.notice_id, notice_table_mock.id)
            self.assertEqual(result.notice_title, notice_table_mock.notice_title)
            self.assertEqual(result.notice_contents, notice_table_mock.notice_contents)
            self.assertEqual(result.begin_date, notice_table_mock.begin_date)
            self.assertEqual(result.end_date, notice_table_mock.end_date)
            self.assertEqual(result.is_urgent, notice_table_mock.is_urgent)
            self.assertEqual(result.is_active, notice_table_mock.is_active)
            self.assertEqual(result.is_exposure, notice_table_mock.is_exposure)
            self.assertEqual(result.creator, notice_table_mock.creator)
            self.assertEqual(result.modified_at, notice_table_mock.modified_at)
            self.assertEqual(result.tenant_id, notice_table_mock.tenant_id)

    def test_select_by_id_error(self):
        db_mock = self.create_db_mock()
        notice_table_mock = self.create_notice_table_mock()

        self.session_mock.query.return_value.get.return_value = []

        with patch('genai.base.common.database.inject_transactional_session'), \
            patch('genai.base.common.database.db', db_mock), \
            patch('genai.system_admin.adapter.outbound.persistence.table.notice_table.NoticeTable.from_domain',
                  return_value=notice_table_mock):
            with pytest.raises(ServerException) as exc_info:
                result = self.repository.select_by_id(1, 1)

            assert exc_info.value.error_code == 'COMMON_ERROR_4'
            assert str(exc_info.value.detail_message) == "The Notice [1] does not exist"

    def test_select_by_id_for_user(self):
        db_mock = self.create_db_mock()
        notice_table_mock = self.create_notice_table_mock()

        self.session_mock.query.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = notice_table_mock

        with patch('genai.base.common.database.inject_transactional_session'), \
            patch('genai.base.common.database.db', db_mock), \
            patch('genai.system_admin.adapter.outbound.persistence.table.notice_table.NoticeTable.from_domain',
                  return_value=notice_table_mock):
            result = self.repository.select_by_id_for_user(1, 1, NoticeConditionStatus.INPROGRESS)
            self.assertIsInstance(result, NoticeDomain)
            self.assertEqual(result.notice_id, notice_table_mock.id)
            self.assertEqual(result.notice_title, notice_table_mock.notice_title)
            self.assertEqual(result.notice_contents, notice_table_mock.notice_contents)
            self.assertEqual(result.begin_date, notice_table_mock.begin_date)
            self.assertEqual(result.end_date, notice_table_mock.end_date)
            self.assertEqual(result.is_urgent, notice_table_mock.is_urgent)
            self.assertEqual(result.is_active, notice_table_mock.is_active)
            self.assertEqual(result.is_exposure, notice_table_mock.is_exposure)
            self.assertEqual(result.creator, notice_table_mock.creator)
            self.assertEqual(result.modified_at, notice_table_mock.modified_at)
            self.assertEqual(result.tenant_id, notice_table_mock.tenant_id)


    def test_select_by_id_for_user_error(self):
        db_mock = self.create_db_mock()
        notice_table_mock = self.create_notice_table_mock()

        self.session_mock.query.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = []

        with patch('genai.base.common.database.inject_transactional_session'), \
            patch('genai.base.common.database.db', db_mock), \
            patch('genai.system_admin.adapter.outbound.persistence.table.notice_table.NoticeTable.from_domain',
                  return_value=notice_table_mock):
            with pytest.raises(ServerException) as exc_info:
                result = self.repository.select_by_id_for_user(1, 1, NoticeConditionStatus.BEFORE)

            assert exc_info.value.error_code == 'COMMON_ERROR_4'
            assert str(exc_info.value.detail_message) == "The Notice [1] does not exist"

    def test_get_notice_page_list(self):
        db_mock = self.create_db_mock()
        notice_table_mock = self.create_notice_table_mock()
        pagination = PaginationParams(page=1, limit=10)

        self.session_mock.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            notice_table_mock]  # Ensure this is a list

        # Set up the mock to return an integer for the total of Page
        self.session_mock.query.return_value.filter.return_value.count.return_value = 1

        with patch('genai.base.common.database.inject_transactional_session'), \
            patch('genai.base.common.database.db', db_mock), \
            patch('genai.system_admin.adapter.outbound.persistence.table.notice_table.NoticeTable.from_domain',
                  return_value=notice_table_mock):

            result = self.repository.get_notice_page_list(tenant_id=1, pagination=pagination)

            self.assertIsInstance(result, Page)
            result_page = dict(dict(result).get("meta"))
            self.assertEqual(result_page.get("totalItems"), 1)
            self.assertEqual(result_page.get("itemCount"), 1)
            self.assertEqual(result_page.get("itemsPerPage"), 10)
            self.assertEqual(result_page.get("currentPage"), 1)
            self.assertEqual(result_page.get("totalPages"), 1)
            result_items = dict(result).get("items")
            self.assertEqual(len(result_items), 1)
            self.assertIsInstance(result_items[0], NoticeDomain)
            self.assertEqual(result_items[0].notice_id, notice_table_mock.id)
            self.assertEqual(result_items[0].notice_title, notice_table_mock.notice_title)
            self.assertEqual(result_items[0].notice_contents, notice_table_mock.notice_contents)
            self.assertEqual(result_items[0].begin_date, notice_table_mock.begin_date)
            self.assertEqual(result_items[0].end_date, notice_table_mock.end_date)
            self.assertEqual(result_items[0].is_urgent, notice_table_mock.is_urgent)
            self.assertEqual(result_items[0].is_active, notice_table_mock.is_active)
            self.assertEqual(result_items[0].is_exposure, notice_table_mock.is_exposure)
            self.assertEqual(result_items[0].creator, notice_table_mock.creator)
            self.assertEqual(result_items[0].modified_at, notice_table_mock.modified_at)
            self.assertEqual(result_items[0].tenant_id, notice_table_mock.tenant_id)

    def test_get_notice_page_list_before(self):
        db_mock = self.create_db_mock()
        notice_table_mock = self.create_notice_table_mock()
        pagination = PaginationParams(page=1, limit=10)

        self.session_mock.query.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            notice_table_mock]  # Ensure this is a list

        # Set up the mock to return an integer for the total of Page
        self.session_mock.query.return_value.filter.return_value.filter.return_value.count.return_value = 1

        with patch('genai.base.common.database.inject_transactional_session'), \
            patch('genai.base.common.database.db', db_mock), \
            patch('genai.system_admin.adapter.outbound.persistence.table.notice_table.NoticeTable.from_domain',
                  return_value=notice_table_mock):
            notice_search_contidtion_paramas = NoticeSearchConditionParams(status=NoticeConditionStatus.BEFORE)
            result = self.repository.get_notice_page_list(condition=notice_search_contidtion_paramas, tenant_id=1, pagination=pagination)

            self.assertIsInstance(result, Page)
            result_page = dict(dict(result).get("meta"))
            self.assertEqual(result_page.get("totalItems"), 1)
            self.assertEqual(result_page.get("itemCount"), 1)
            self.assertEqual(result_page.get("itemsPerPage"), 10)
            self.assertEqual(result_page.get("currentPage"), 1)
            self.assertEqual(result_page.get("totalPages"), 1)
            result_items = dict(result).get("items")
            self.assertEqual(len(result_items), 1)
            self.assertIsInstance(result_items[0], NoticeDomain)
            self.assertEqual(result_items[0].notice_id, notice_table_mock.id)
            self.assertEqual(result_items[0].notice_title, notice_table_mock.notice_title)
            self.assertEqual(result_items[0].notice_contents, notice_table_mock.notice_contents)
            self.assertEqual(result_items[0].begin_date, notice_table_mock.begin_date)
            self.assertEqual(result_items[0].end_date, notice_table_mock.end_date)
            self.assertEqual(result_items[0].is_urgent, notice_table_mock.is_urgent)
            self.assertEqual(result_items[0].is_active, notice_table_mock.is_active)
            self.assertEqual(result_items[0].is_exposure, notice_table_mock.is_exposure)
            self.assertEqual(result_items[0].creator, notice_table_mock.creator)
            self.assertEqual(result_items[0].modified_at, notice_table_mock.modified_at)
            self.assertEqual(result_items[0].tenant_id, notice_table_mock.tenant_id)

    def test_get_notice_page_list_inprogress(self):
        db_mock = self.create_db_mock()
        notice_table_mock = self.create_notice_table_mock()
        pagination = PaginationParams(page=1, limit=10)

        self.session_mock.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            notice_table_mock]  # Ensure this is a list

        # Set up the mock to return an integer for the total of Page
        self.session_mock.query.return_value.filter.return_value.filter.return_value.filter.return_value.count.return_value = 1

        with patch('genai.base.common.database.inject_transactional_session'), \
            patch('genai.base.common.database.db', db_mock), \
            patch('genai.system_admin.adapter.outbound.persistence.table.notice_table.NoticeTable.from_domain',
                  return_value=notice_table_mock):
            notice_search_contidtion_paramas = NoticeSearchConditionParams(status=NoticeConditionStatus.INPROGRESS)
            result = self.repository.get_notice_page_list(condition=notice_search_contidtion_paramas, tenant_id=1, pagination=pagination)

            self.assertIsInstance(result, Page)
            result_page = dict(dict(result).get("meta"))
            self.assertEqual(result_page.get("totalItems"), 1)
            self.assertEqual(result_page.get("itemCount"), 1)
            self.assertEqual(result_page.get("itemsPerPage"), 10)
            self.assertEqual(result_page.get("currentPage"), 1)
            self.assertEqual(result_page.get("totalPages"), 1)
            result_items = dict(result).get("items")
            self.assertEqual(len(result_items), 1)
            self.assertIsInstance(result_items[0], NoticeDomain)
            self.assertEqual(result_items[0].notice_id, notice_table_mock.id)
            self.assertEqual(result_items[0].notice_title, notice_table_mock.notice_title)
            self.assertEqual(result_items[0].notice_contents, notice_table_mock.notice_contents)
            self.assertEqual(result_items[0].begin_date, notice_table_mock.begin_date)
            self.assertEqual(result_items[0].end_date, notice_table_mock.end_date)
            self.assertEqual(result_items[0].is_urgent, notice_table_mock.is_urgent)
            self.assertEqual(result_items[0].is_active, notice_table_mock.is_active)
            self.assertEqual(result_items[0].is_exposure, notice_table_mock.is_exposure)
            self.assertEqual(result_items[0].creator, notice_table_mock.creator)
            self.assertEqual(result_items[0].modified_at, notice_table_mock.modified_at)
            self.assertEqual(result_items[0].tenant_id, notice_table_mock.tenant_id)

    def test_get_notice_page_list_inactive(self):
        db_mock = self.create_db_mock()
        notice_table_mock = self.create_notice_table_mock()
        pagination = PaginationParams(page=1, limit=10)

        self.session_mock.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            notice_table_mock]  # Ensure this is a list

        # Set up the mock to return an integer for the total of Page
        self.session_mock.query.return_value.filter.return_value.filter.return_value.filter.return_value.count.return_value = 1

        with patch('genai.base.common.database.inject_transactional_session'), \
            patch('genai.base.common.database.db', db_mock), \
            patch('genai.system_admin.adapter.outbound.persistence.table.notice_table.NoticeTable.from_domain',
                  return_value=notice_table_mock):
            notice_search_contidtion_paramas = NoticeSearchConditionParams(status=NoticeConditionStatus.INACTIVE)
            result = self.repository.get_notice_page_list(condition=notice_search_contidtion_paramas, tenant_id=1, pagination=pagination)

            self.assertIsInstance(result, Page)
            result_page = dict(dict(result).get("meta"))
            self.assertEqual(result_page.get("totalItems"), 1)
            self.assertEqual(result_page.get("itemCount"), 1)
            self.assertEqual(result_page.get("itemsPerPage"), 10)
            self.assertEqual(result_page.get("currentPage"), 1)
            self.assertEqual(result_page.get("totalPages"), 1)
            result_items = dict(result).get("items")
            self.assertEqual(len(result_items), 1)
            self.assertIsInstance(result_items[0], NoticeDomain)
            self.assertEqual(result_items[0].notice_id, notice_table_mock.id)
            self.assertEqual(result_items[0].notice_title, notice_table_mock.notice_title)
            self.assertEqual(result_items[0].notice_contents, notice_table_mock.notice_contents)
            self.assertEqual(result_items[0].begin_date, notice_table_mock.begin_date)
            self.assertEqual(result_items[0].end_date, notice_table_mock.end_date)
            self.assertEqual(result_items[0].is_urgent, notice_table_mock.is_urgent)
            self.assertEqual(result_items[0].is_active, notice_table_mock.is_active)
            self.assertEqual(result_items[0].is_exposure, notice_table_mock.is_exposure)
            self.assertEqual(result_items[0].creator, notice_table_mock.creator)
            self.assertEqual(result_items[0].modified_at, notice_table_mock.modified_at)
            self.assertEqual(result_items[0].tenant_id, notice_table_mock.tenant_id)

    def test_get_notice_page_list_expired(self):
        db_mock = self.create_db_mock()
        notice_table_mock = self.create_notice_table_mock()
        pagination = PaginationParams(page=1, limit=10)

        self.session_mock.query.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            notice_table_mock]  # Ensure this is a list

        # Set up the mock to return an integer for the total of Page
        self.session_mock.query.return_value.filter.return_value.filter.return_value.count.return_value = 1

        with patch('genai.base.common.database.inject_transactional_session'), \
            patch('genai.base.common.database.db', db_mock), \
            patch('genai.system_admin.adapter.outbound.persistence.table.notice_table.NoticeTable.from_domain',
                  return_value=notice_table_mock):
            notice_search_contidtion_paramas = NoticeSearchConditionParams(status=NoticeConditionStatus.EXPIRED)
            result = self.repository.get_notice_page_list(condition=notice_search_contidtion_paramas, tenant_id=1, pagination=pagination)

            self.assertIsInstance(result, Page)
            result_page = dict(dict(result).get("meta"))
            self.assertEqual(result_page.get("totalItems"), 1)
            self.assertEqual(result_page.get("itemCount"), 1)
            self.assertEqual(result_page.get("itemsPerPage"), 10)
            self.assertEqual(result_page.get("currentPage"), 1)
            self.assertEqual(result_page.get("totalPages"), 1)
            result_items = dict(result).get("items")
            self.assertEqual(len(result_items), 1)
            self.assertIsInstance(result_items[0], NoticeDomain)
            self.assertEqual(result_items[0].notice_id, notice_table_mock.id)
            self.assertEqual(result_items[0].notice_title, notice_table_mock.notice_title)
            self.assertEqual(result_items[0].notice_contents, notice_table_mock.notice_contents)
            self.assertEqual(result_items[0].begin_date, notice_table_mock.begin_date)
            self.assertEqual(result_items[0].end_date, notice_table_mock.end_date)
            self.assertEqual(result_items[0].is_urgent, notice_table_mock.is_urgent)
            self.assertEqual(result_items[0].is_active, notice_table_mock.is_active)
            self.assertEqual(result_items[0].is_exposure, notice_table_mock.is_exposure)
            self.assertEqual(result_items[0].creator, notice_table_mock.creator)
            self.assertEqual(result_items[0].modified_at, notice_table_mock.modified_at)
            self.assertEqual(result_items[0].tenant_id, notice_table_mock.tenant_id)

    def test_get_notice_page_list_error(self):
        db_mock = self.create_db_mock()
        notice_table_mock = self.create_notice_table_mock()
        pagination = PaginationParams(page=1, limit=10)

        self.session_mock.query.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            notice_table_mock]  # Ensure this is a list

        # Set up the mock to return an integer for the total of Page
        self.session_mock.query.return_value.filter.return_value.filter.return_value.count.return_value = 1

        with patch('genai.base.common.database.inject_transactional_session'), \
            patch('genai.base.common.database.db', db_mock), \
            patch('genai.system_admin.adapter.outbound.persistence.table.notice_table.NoticeTable.from_domain',
                  return_value=notice_table_mock):
            notice_search_contidtion_paramas = NoticeSearchConditionParams(status=NoticeConditionStatus.ERROR)
            with pytest.raises(ServerException) as exc_info:
                result = self.repository.get_notice_page_list(condition=notice_search_contidtion_paramas, tenant_id=1, pagination=pagination)

            assert exc_info.value.error_code == 'COMMON_ERROR_4'
            assert str(exc_info.value.detail_message) == "The Notice Status [ERROR] does not exist"

    def test_get_notice_page_list_for_user(self):
        db_mock = self.create_db_mock()
        notice_table_mock = self.create_notice_table_mock()
        pagination = PaginationParams(page=1, limit=10)

        self.session_mock.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            notice_table_mock]

        # Set up the mock to return an integer for the total of Page
        self.session_mock.query.return_value.filter.return_value.filter.return_value.filter.return_value.count.return_value = 1

        with patch('genai.base.common.database.inject_transactional_session'), \
            patch('genai.base.common.database.db', db_mock), \
            patch('genai.system_admin.adapter.outbound.persistence.table.notice_table.NoticeTable.from_domain',
                  return_value=notice_table_mock):
            result = self.repository.get_notice_page_list_for_user("INPROGRESS", True, 1, pagination)
            self.assertIsInstance(result, Page)
            result_items = dict(result).get("items")
            self.assertEqual(len(result_items), 1)
            self.assertIsInstance(result_items[0], NoticeDomain)
            self.assertEqual(result_items[0].notice_id, notice_table_mock.id)
            self.assertEqual(result_items[0].notice_title, notice_table_mock.notice_title)
            self.assertEqual(result_items[0].notice_contents, notice_table_mock.notice_contents)
            self.assertEqual(result_items[0].begin_date, notice_table_mock.begin_date)
            self.assertEqual(result_items[0].end_date, notice_table_mock.end_date)
            self.assertEqual(result_items[0].is_urgent, notice_table_mock.is_urgent)
            self.assertEqual(result_items[0].is_active, notice_table_mock.is_active)
            self.assertEqual(result_items[0].is_exposure, notice_table_mock.is_exposure)
            self.assertEqual(result_items[0].creator, notice_table_mock.creator)
            self.assertEqual(result_items[0].modified_at, notice_table_mock.modified_at)
            self.assertEqual(result_items[0].tenant_id, notice_table_mock.tenant_id)

    def test_get_notice_page_list_for_user_error(self):
        db_mock = self.create_db_mock()
        notice_table_mock = self.create_notice_table_mock()
        pagination = PaginationParams(page=1, limit=10)

        self.session_mock.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            notice_table_mock]

        # Set up the mock to return an integer for the total of Page
        self.session_mock.query.return_value.filter.return_value.filter.return_value.filter.return_value.count.return_value = 1

        with patch('genai.base.common.database.inject_transactional_session'), \
            patch('genai.base.common.database.db', db_mock), \
            patch('genai.system_admin.adapter.outbound.persistence.table.notice_table.NoticeTable.from_domain',
                  return_value=notice_table_mock):
            with pytest.raises(ServerException) as exc_info:
                result = self.repository.get_notice_page_list_for_user("BEFORE", True, 1, pagination)

            assert exc_info.value.error_code == 'COMMON_ERROR_7'
            assert str(exc_info.value.detail_message) == "The Notice Status [BEFORE] Access is denied"

if __name__ == '__main__':
    # for vanilla unittest
    # unittest.main()
    # for all tests with pytest
    pytest.main(["-s", "-v", __file__ ])
    # for a specific pytest function
    # pytest.main(["-s", "-v", __file__ + "::test_specific"])
