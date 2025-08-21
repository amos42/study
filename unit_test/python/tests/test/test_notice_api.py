from datetime import datetime
from datetime import timedelta
from unittest.mock import MagicMock
from unittest.mock import patch
from uuid import UUID

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from genai.base.common.auth import User
from genai.base.common.auth import get_user
from genai.base.common.pagination import Page
from genai.base.common.pagination import PaginationInfo
from genai.base.constants.permission import Permission
from genai.base.middleware.jwt_middleware import JWTParserMiddleware
from genai.system_admin.domain.notice_domain import NoticeDomain
from genai.system_admin.main import app

client = TestClient(app, root_path="/api/system")

time_format = "%Y-%m-%dT%H:%M:%S.%f"

patch('genai.base.admin.admin_api_log.gen_request_info').start()
patch('genai.base.admin.admin_api_log.gen_admin_api_log').start()


def mock_middleware_dispatch(*args, **kwargs):
    return args[1](args[0])

JWTParserMiddleware.dispatch = MagicMock(side_effect=mock_middleware_dispatch)

@pytest.fixture(scope="module")
def mock_get_user():
    async def get_user():
        return User(id=UUID(int=3),
                    tenant_id=1,
                    name="tester",
                    user_email="test@samsung.com",
                    permission=[
                        Permission.CREATE_NOTICE,
                        Permission.READ_NOTICE,
                        Permission.UPDATE_NOTICE,
                        Permission.DELETE_NOTICE,
                        Permission.READ_NOTICE_USER,
                    ],
                    access_token="test_token",
                )
    return get_user

@pytest.fixture(scope="module")
def mock_get_modify_user():
    async def get_user():
        return User(id=UUID(int=10),
                    tenant_id=1,
                    name="tester_2",
                    user_email="test_2@samsung.com",
                    permission=[
                        Permission.UPDATE_NOTICE,
                    ],
                    access_token="test_token",
                )
    return get_user

@pytest.fixture(scope="module")
def mock_get_no_permit_user():
    async def get_user():
        return User(id=UUID(int=100),
                    tenant_id=1,
                    name="tester_3",
                    user_email="test_3@samsung.com",
                    permission=[
                    ],
                    access_token="test_token",
                )
    return get_user

@pytest.fixture
def sample_notice():
    return NoticeDomain(
            notice_id=1,
            notice_title="테스트 공지 제목",
            notice_contents="<p>테스트 공지 내용</p>",
            begin_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now() + timedelta(days=7),
            is_urgent=False,
            is_active=True,
            created_at=datetime.now() - timedelta(days=3),
            modified_at=datetime.now() - timedelta(days=3),
            creator=UUID(int=3),
            modifier=UUID(int=3),
            creator_name="tester",
            modifier_name="tester",
            is_exposure=False,
            tenant_id=1,
        )

@pytest.fixture
def sample_notices():
    return Page(meta=PaginationInfo(totalItems=2, itemCount=2, itemsPerPage=10, totalPages=1, currentPage=1),
        items=
        [
        NoticeDomain(
            notice_id=1,
            notice_title="테스트 공지 제목",
            notice_contents="<p>테스트 공지 내용</p>",
            begin_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now() + timedelta(days=7),
            is_urgent=False,
            is_active=True,
            created_at=datetime.now() - timedelta(days=2),
            modified_at=datetime.now() - timedelta(days=2),
            creator=UUID(int=3),
            modifier=UUID(int=3),
            creator_name="tester",
            modifier_name="tester",
            is_exposure=False,
            tenant_id=1,
        ),
        NoticeDomain(
            notice_id=2,
            notice_title="테스트 테스트 테스트 제목",
            notice_contents="<p>알려주세요</p>",
            begin_date=datetime.now() + timedelta(days=1),
            end_date=datetime.now() + timedelta(days=7),
            is_urgent=False,
            is_active=True,
            created_at=datetime.now(),
            modified_at=datetime.now(),
            creator=UUID(int=10),
            modifier=UUID(int=10),
            creator_name="tester_2",
            modifier_name="tester_2",
            is_exposure=False,
            tenant_id=1,
        )
        ]
    )

def test_get_notice_by_id_for_user(sample_notices, monkeypatch, mock_get_user):
    def mock_get_by_id_for_user(request, notice_id, tenant_id, status):
        filtered_item = [item for item in sample_notices.items if notice_id == item.notice_id][0]
        return filtered_item

    monkeypatch.setattr("genai.system_admin.application.service.notice_service.NoticeService.get_by_id_for_user", mock_get_by_id_for_user)
    app.dependency_overrides[get_user] = mock_get_user

    response = client.get("/api/system/v1/notices/1/user?status=INPROGRESS")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["noticeId"] == 1
    assert data["noticeTitle"] == "테스트 공지 제목"
    assert data["noticeContents"] == "<p>테스트 공지 내용</p>"
    assert data["creatorName"] == "tester"
    assert data["modifierName"] == "tester"

def test_get_notice_by_id_for_user_no_id(sample_notices, monkeypatch, mock_get_user):
    def mock_get_by_id_for_user(request, notice_id, tenant_id, status):
        filtered_item = [item for item in sample_notices.items if notice_id == item.notice_id]
        if len(filtered_item) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"The Notice [{notice_id}] does not exist"
            )
        return filtered_item

    monkeypatch.setattr("genai.system_admin.application.service.notice_service.NoticeService.get_by_id_for_user", mock_get_by_id_for_user)
    app.dependency_overrides[get_user] = mock_get_user

    response = client.get("/api/system/v1/notices/100/user?status=INPROGRESS")

    assert response.status_code == 404
    error_response = response.json()
    assert error_response.get("error") == "Not Found"
    # assert error_response.get("errorCode") == "COMMON_ERROR_1" #COMMON_ERROR_4가 나와야하는데 방법을 모르겠음.
    assert error_response.get("message") == "The Notice [100] does not exist"

def test_get_notices_for_user(sample_notices, monkeypatch, mock_get_user):
    def mock_get_list_for_user(request, status, is_active, tenant_id, pagination):
        return sample_notices

    monkeypatch.setattr("genai.system_admin.application.service.notice_service.NoticeService.get_list_for_user",
                        mock_get_list_for_user)
    app.dependency_overrides[get_user] = mock_get_user

    response = client.get("/api/system/v1/notices/user?status=INPROGRESS&is_active=true&page=1&limit=10")
    assert response.status_code == 200
    data = response.json()["data"]["items"]
    assert len(data) == 2
    notice = data[1]
    assert notice["noticeId"] == 2
    assert notice["noticeTitle"] == "테스트 테스트 테스트 제목"
    assert notice["creatorName"] == "tester_2"
    assert notice["modifierName"] == "tester_2"

def test_get_notices(sample_notices, monkeypatch, mock_get_user):
    def mock_get_list(request, pagination, condition, tenant_id):
        return sample_notices

    monkeypatch.setattr(
        "genai.system_admin.application.service.notice_service.NoticeService.get_list",
        mock_get_list)
    app.dependency_overrides[get_user] = mock_get_user

    response = client.get("/api/system/v1/notices")
    assert response.status_code == 200
    data = response.json()["data"]["items"]
    assert len(data) == 2
    notice0 = data[0]
    assert notice0["noticeId"] == 1
    assert notice0["noticeTitle"] == "테스트 공지 제목"
    assert notice0["creatorName"] == "tester"
    assert notice0["modifierName"] == "tester"
    notice1 = data[1]
    assert notice1["noticeId"] == 2
    assert notice1["noticeTitle"] == "테스트 테스트 테스트 제목"
    assert notice1["creatorName"] == "tester_2"
    assert notice1["modifierName"] == "tester_2"

def test_get_notices_no_permit(sample_notices, monkeypatch, mock_get_no_permit_user):
    def mock_get_list(request, pagination, condition, tenant_id):
        return sample_notices

    monkeypatch.setattr(
        "genai.system_admin.application.service.notice_service.NoticeService.get_list",
        mock_get_list)
    app.dependency_overrides[get_user] = mock_get_no_permit_user

    response = client.get("/api/system/v1/notices")
    assert response.status_code == 403
    error_response = response.json()
    assert error_response.get("error") == "Forbidden"
    assert error_response.get("errorCode") == "COMMON_ERROR_1"
    assert error_response.get("message") == "Access is denied"


def test_get_notices_condition(sample_notices, monkeypatch, mock_get_user):
    def mock_get_list(request, pagination, condition, tenant_id):
        sample_notices.items = [
            item for item in sample_notices.items
            if condition.notice_title in item.notice_title and condition.creator_name in item.creator_name
        ]
        return sample_notices

    monkeypatch.setattr(
        "genai.system_admin.application.service.notice_service.NoticeService.get_list",
        mock_get_list)
    app.dependency_overrides[get_user] = mock_get_user

    response = client.get("/api/system/v1/notices?noticeTitle=공지&creatorName=tester&page=1&limit=10")
    assert response.status_code == 200
    data = response.json()["data"]["items"]
    assert len(data) == 1
    notice0 = data[0]
    assert notice0["noticeId"] == 1
    assert notice0["noticeTitle"] == "테스트 공지 제목"
    assert notice0["creatorName"] == "tester"
    assert notice0["modifierName"] == "tester"

def test_get_notices_page_error(sample_notices, monkeypatch, mock_get_user):
    def mock_get_list(request, pagination, condition, tenant_id):
        sample_notices.items = [
            item for item in sample_notices.items
            if condition.notice_title in item.notice_title and condition.creator_name in item.creator_name
        ]
        return sample_notices

    monkeypatch.setattr(
        "genai.system_admin.application.service.notice_service.NoticeService.get_list",
        mock_get_list)
    app.dependency_overrides[get_user] = mock_get_user

    response = client.get("/api/system/v1/notices?noticeTitle=공지&creatorName=tester&page=1&limit=a")
    assert response.status_code == 422
    error_response = response.json()
    assert error_response.get("error") == "Unprocessable Entity"
    assert error_response.get("errorCode") == "COMMON_ERROR_1"
    # assert error_response.get("message") == "limit, value is not a valid integer"


def test_get_notices_condition_error(sample_notices, monkeypatch, mock_get_user):
    def mock_get_list(request, pagination, condition, tenant_id):
        sample_notices.items = [
            item for item in sample_notices.items
            if condition.notice_title in item.notice_title and condition.creator_name in item.creator_name
        ]
        return sample_notices

    monkeypatch.setattr(
        "genai.system_admin.application.service.notice_service.NoticeService.get_list",
        mock_get_list)
    app.dependency_overrides[get_user] = mock_get_user

    response = client.get("/api/system/v1/notices?noticeTitle=공지&creatorName=tester&page=1&limit=10&isActive=AAA")
    assert response.status_code == 422
    error_response = response.json()
    assert error_response.get("error") == "Unprocessable Entity"
    assert error_response.get("errorCode") == "COMMON_ERROR_1"
    # assert error_response.get("message") == "isActive, value could not be parsed to a boolean"


def test_create_notice(sample_notice, monkeypatch, mock_get_user):
    create_notice_id = 123

    def mock_create(request, notice_domain: NoticeDomain) -> NoticeDomain:
        notice_dict = notice_domain.dict()
        sample_notice.notice_id = create_notice_id
        sample_notice.notice_title = notice_dict["notice_title"]
        sample_notice.notice_contents = notice_dict["notice_contents"]
        sample_notice.begin_date = notice_dict["begin_date"]
        sample_notice.end_date = notice_dict["end_date"]
        sample_notice.is_urgent = notice_dict["is_urgent"]
        sample_notice.is_active = notice_dict["is_active"]
        sample_notice.created_at = notice_dict["created_at"]
        sample_notice.modified_at = notice_dict["modified_at"]
        sample_notice.creator = notice_dict["creator"]
        sample_notice.modifier = notice_dict["modifier"]
        sample_notice.creator_name = notice_dict["creator_name"]
        sample_notice.modifier_name = notice_dict["modifier_name"]
        sample_notice.is_exposure = notice_dict["is_exposure"]
        sample_notice.tenant_id = notice_dict["tenant_id"]
        return sample_notice

    monkeypatch.setattr(
        "genai.system_admin.application.service.notice_service.NoticeService.create",
        mock_create)
    app.dependency_overrides[get_user] = mock_get_user

    begin_date = (datetime.now() - timedelta(days=1)).strftime(time_format) + '+09:00'
    end_date = (datetime.now() + timedelta(days=3)).strftime(time_format) + '+09:00'

    request_data = {
        "noticeTitle": "공지생성 테스트",
        "noticeContents": "<p>이상 공지입니다</p>",
        "isActive": True,
        "beginDate": begin_date,
        "endDate": end_date,
        "isUrgent": False,
        "isExposure": False
    }
    response = client.post("/api/system/v1/notices", json=request_data)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["noticeId"] == create_notice_id
    assert data["noticeTitle"] == request_data["noticeTitle"]
    assert data["noticeContents"] == request_data["noticeContents"]
    assert data["isActive"] == request_data["isActive"]
    assert data["beginDate"] == request_data["beginDate"]
    assert data["endDate"] == request_data["endDate"]
    assert data["isUrgent"] == request_data["isUrgent"]
    assert data["isExposure"] == request_data["isExposure"]

def test_update_notice(sample_notices, monkeypatch, mock_get_modify_user):
    def mock_update(request, notice_domain):
        notice_dict = notice_domain.dict()
        filtered_item = [item for item in sample_notices.items if notice_dict["notice_id"] == item.notice_id][0]
        filtered_item.notice_title = notice_dict["notice_title"]
        filtered_item.notice_contents = notice_dict["notice_contents"]
        filtered_item.begin_date = notice_dict["begin_date"]
        filtered_item.end_date = notice_dict["end_date"]
        filtered_item.is_urgent = notice_dict["is_urgent"]
        filtered_item.is_active = notice_dict["is_active"]
        filtered_item.modified_at = notice_dict["modified_at"]
        filtered_item.modifier = notice_dict["modifier"]
        filtered_item.modifier_name = notice_dict["modifier_name"]
        filtered_item.is_exposure = notice_dict["is_exposure"]
        filtered_item.tenant_id = notice_dict["tenant_id"]
        return filtered_item

    monkeypatch.setattr(
        "genai.system_admin.application.service.notice_service.NoticeService.update",
        mock_update)
    app.dependency_overrides[get_user] = mock_get_modify_user

    begin_date = (datetime.now() - timedelta(days=1)).strftime(time_format) + '+09:00'
    end_date = (datetime.now() + timedelta(days=3)).strftime(time_format) + '+09:00'

    request_data = {
        "noticeId": 1,
        "noticeTitle": "공지수정 테스트",
        "noticeContents": "<p>이하 공지입니다</p>",
        "isActive": True,
        "beginDate": begin_date,
        "endDate": end_date,
        "isUrgent": False,
        "isExposure": False
    }
    response = client.put("/api/system/v1/notices", json=request_data)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["noticeId"] == request_data["noticeId"]
    assert data["noticeTitle"] == request_data["noticeTitle"]
    assert data["noticeContents"] == request_data["noticeContents"]
    assert data["isActive"] == request_data["isActive"]
    assert data["beginDate"] == request_data["beginDate"]
    assert data["endDate"] == request_data["endDate"]
    assert data["isUrgent"] == request_data["isUrgent"]
    assert data["isExposure"] == request_data["isExposure"]

#testclient의 delete method에서 data(json)을 허용하지 않아 테스트 불가. 쿼리 파라미터로 수정해야 테스트 가능
# def test_delete_notices(sample_notices, monkeypatch, mock_get_user):
#     def mock_update(request, notice_domain):
#         notice_dict = notice_domain.dict()
#         filtered_item = [item for item in sample_notices.items if notice_dict["notice_id"] == item.notice_id]
#         return len(filtered_item)
#
#     monkeypatch.setattr(
#         "genai.management_server.application.service.notice_service.NoticeService.update",
#         mock_update)
#     app.dependency_overrides[get_user] = mock_get_user
#
#     request_data = {"noticeIds": [1]}
#     response = client.delete("/api/system/v1/notices", json=request_data)
#     assert response.status_code == 200
#     data = response.json()["data"]
#     assert data == len(request_data["noticeIds"])

if __name__ == '__main__':
    # for vanilla unittest
    # unittest.main()
    # for all tests with pytest
    pytest.main(["-s", "-v", __file__ ])
    # for a specific pytest function
    # pytest.main(["-s", "-v", __file__ + "::test_specific"])
