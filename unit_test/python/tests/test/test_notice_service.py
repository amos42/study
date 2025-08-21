from datetime import datetime
from datetime import timedelta
from http import HTTPStatus
from unittest.mock import Mock
from uuid import UUID

import pytest

from genai.base.common.exception import ServerException
from genai.base.common.pagination import PaginationParams
from genai.system_admin.adapter.outbound.persistence.notice_repository import NoticeRepository
from genai.system_admin.application.condition import NoticeSearchConditionParams
from genai.system_admin.application.service.notice_service import NoticeService
from genai.system_admin.domain.notice_domain import NoticeDomain

sample_notice = NoticeDomain(
    notice_id=1,
    notice_title="Sample Notice",
    notice_contents="This is a sample notice.",
    begin_date=datetime.now() - timedelta(days=1),
    end_date=datetime.now() + timedelta(days=7),
    is_urgent=False,
    is_active=True,
    is_exposure=False,
    creator=UUID(int=0),
    created_at=datetime.now(),
    modifier=UUID(int=0),
    modified_at=datetime.now(),
    tenant_id=1
)


@pytest.fixture
def mock_repository():
    mock_repo = Mock(spec=NoticeRepository)
    mock_repo.create.side_effect = lambda x: x  # Return the input argument itself
    mock_repo.update.side_effect = lambda x: x  # Return the input argument itself
    mock_repo.delete.side_effect = lambda x: sample_notice  # Return a fixed sample notice
    mock_repo.get_notice_page_list.return_value = [sample_notice]
    mock_repo.get_notice_page_list_for_user.return_value = [sample_notice]
    mock_repo.select_by_id.return_value = sample_notice
    mock_repo.select_by_id_for_user.return_value = sample_notice
    mock_repo.delete_notice_list.side_effect = lambda ids, tenant_id: len(ids)  # Simulate successful deletion
    return mock_repo


@pytest.fixture
def notice_service(mock_repository):
    return NoticeService(repository=mock_repository)


def test_create_notice(notice_service):
    new_notice = NoticeDomain(
        notice_id=2,
        notice_title="New Notice",
        notice_contents="This is a new notice.",
        begin_date=datetime.now() - timedelta(days=2),
        end_date=datetime.now() + timedelta(days=5),
        is_urgent=False,
        is_active=True,
        is_exposure=False,
        creator=UUID(int=100),
        created_at=datetime.now(),
        modifier=UUID(int=100),
        modified_at=datetime.now(),
        tenant_id=1
    )
    result = notice_service.create(new_notice)

    # Verify that the create method was called with the correct arguments
    notice_service._repository.create.assert_called_once_with(new_notice)

    # Check that the returned value matches the input notice
    assert result.notice_id == new_notice.notice_id
    assert result.notice_title == new_notice.notice_title
    assert result.notice_contents == new_notice.notice_contents
    assert result.begin_date == new_notice.begin_date
    assert result.end_date == new_notice.end_date
    assert result.is_urgent == new_notice.is_urgent
    assert result.is_active == new_notice.is_active
    assert result.is_exposure == new_notice.is_exposure
    assert result.creator == new_notice.creator
    assert result.created_at == new_notice.created_at
    assert result.modifier == new_notice.modifier
    assert result.modified_at == new_notice.modified_at
    assert result.tenant_id == new_notice.tenant_id


def test_update_notice(notice_service):
    original_creator = sample_notice.creator
    original_created_at = sample_notice.created_at

    updated_notice = NoticeDomain(
        notice_id=1,
        notice_title="Updated Notice",
        notice_contents="This is an updated notice.",
        begin_date=datetime.now() - timedelta(days=3),
        end_date=datetime.now() + timedelta(days=4),
        is_urgent=True,
        is_active=False,
        is_exposure=True,
        creator=original_creator,  # Keep the original creator
        created_at=original_created_at,  # Keep the original creation date
        modifier=UUID(int=200),
        modified_at=datetime.now(),
        tenant_id=1
    )
    result = notice_service.update(updated_notice)

    # Verify that the update method was called with the correct arguments
    notice_service._repository.update.assert_called_once_with(updated_notice)

    # Check that the returned value matches the input notice except for creator and created_at
    assert result.notice_id == updated_notice.notice_id
    assert result.notice_title == updated_notice.notice_title
    assert result.notice_contents == updated_notice.notice_contents
    assert result.begin_date == updated_notice.begin_date
    assert result.end_date == updated_notice.end_date
    assert result.is_urgent == updated_notice.is_urgent
    assert result.is_active == updated_notice.is_active
    assert result.is_exposure == updated_notice.is_exposure
    assert result.creator == original_creator  # Ensure creator remains unchanged
    assert result.created_at == original_created_at  # Ensure created_at remains unchanged
    assert result.modifier == updated_notice.modifier
    assert result.modified_at == updated_notice.modified_at
    assert result.tenant_id == updated_notice.tenant_id


def test_delete_notice(notice_service):
    # Mock the repository's delete method to return the sample notice
    notice_service._repository.delete.return_value = sample_notice

    result = notice_service.delete(1, 1)

    # Verify that the delete method was called with the correct arguments
    notice_service._repository.delete.assert_called_once_with(1)

    # Check that the returned value matches the expected tuple format
    assert result == (sample_notice.notice_id, "success")


def test_delete_nonexistent_notice(notice_service):
    # Mock the repository's delete method to raise an exception
    notice_service._repository.delete.side_effect = ServerException.of("The Notice [999] does not exist", HTTPStatus.NOT_FOUND)

    with pytest.raises(ServerException) as exc_info:
        notice_service.delete(999, 1)

    # Verify that the exception message is correct
    assert exc_info.value.message == "It does not exist"


def test_get_list(notice_service):
    pagination = PaginationParams(page=1, limit=10)
    condition = NoticeSearchConditionParams()
    result = notice_service.get_list(pagination=pagination, condition=condition, tenant_id=1)

    # Verify that the get_notice_page_list method was called with the correct arguments
    notice_service._repository.get_notice_page_list.assert_called_once_with(pagination, condition, 1)

    # Check that the returned value contains the sample notice
    assert len(result) == 1
    assert result[0].notice_id == sample_notice.notice_id


def test_get_list_without_pagination(notice_service):
    condition = NoticeSearchConditionParams()
    result = notice_service.get_list(condition=condition, tenant_id=1)

    # Verify that the get_notice_page_list method was called with the correct arguments
    notice_service._repository.get_notice_page_list.assert_called_once_with(condition, 1)

    # Check that the returned value contains the sample notice
    assert len(result) == 1
    assert result[0].notice_id == sample_notice.notice_id


def test_get_list_for_user(notice_service):
    pagination = PaginationParams(page=1, limit=10)
    result = notice_service.get_list_for_user("INPROGRESS", True, 1, pagination=pagination)

    # Verify that the get_notice_page_list_for_user method was called with the correct arguments
    notice_service._repository.get_notice_page_list_for_user.assert_called_once_with(
        "INPROGRESS", True, 1, pagination
    )

    # Check that the returned value contains the sample notice
    assert len(result) == 1
    assert result[0].notice_id == sample_notice.notice_id


def test_get_list_for_user_without_pagination(notice_service):
    result = notice_service.get_list_for_user("INPROGRESS", True, 1)

    # Verify that the get_notice_page_list_for_user method was called with the correct arguments
    notice_service._repository.get_notice_page_list_for_user.assert_called_once_with(
        "INPROGRESS", True, 1
    )

    # Check that the returned value contains the sample notice
    assert len(result) == 1
    assert result[0].notice_id == sample_notice.notice_id


def test_get_by_id(notice_service):
    result = notice_service.get_by_id(1, 1)

    # Verify that the select_by_id method was called with the correct arguments
    notice_service._repository.select_by_id.assert_called_once_with(1, 1)

    # Check that the returned value matches the sample notice
    assert result.notice_id == sample_notice.notice_id


def test_get_by_id_for_user(notice_service):
    result = notice_service.get_by_id_for_user(1, 1, "INPROGRESS")

    # Verify that the select_by_id_for_user method was called with the correct arguments
    notice_service._repository.select_by_id_for_user.assert_called_once_with(1, 1, "INPROGRESS")

    # Check that the returned value matches the sample notice
    assert result.notice_id == sample_notice.notice_id


def test_delete_notice_list_successfully(notice_service):
    # Mock the repository's delete_notice_list method to return the length of the list
    notice_service._repository.delete_notice_list.side_effect = lambda ids, tenant_id: len(ids)

    result = notice_service.delete_notice_list([1], 1)

    # Verify that the delete_notice_list method was called with the correct arguments
    notice_service._repository.delete_notice_list.assert_called_once_with([1], 1)

    # Check that the returned value matches the number of notices deleted
    assert result == 1


def test_delete_notice_list_with_nonexistent_ids(notice_service):
    # Mock the repository's delete_notice_list method to raise an exception
    notice_service._repository.delete_notice_list.side_effect = ServerException.of("The rules [1, 2] do not exist", HTTPStatus.NOT_FOUND)

    with pytest.raises(ServerException) as exc_info:
        notice_service.delete_notice_list([1, 2], 1)

    # Verify that the exception message is correct
    assert exc_info.value.message == "It does not exist"

if __name__ == '__main__':
    # for vanilla unittest
    # unittest.main()
    # for all tests with pytest
    pytest.main(["-s", "-v", __file__ ])
    # for a specific pytest function
    # pytest.main(["-s", "-v", __file__ + "::test_specific"])
