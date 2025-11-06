from datetime import UTC
from datetime import datetime
from unittest.mock import MagicMock
from unittest.mock import patch
from urllib import parse
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from genai.base.common.auth import User
from genai.base.common.auth import get_user
from genai.base.common.exception import BusinessException
from genai.base.common.exception import ServerException
from genai.base.common.pagination import Page
from genai.base.common.pagination import PaginationParams
from genai.base.constants.error_code import ErrorCode
from genai.base.constants.permission import Permission
from genai.base.middleware.jwt_middleware import JWTParserMiddleware
from genai.system_admin.application.service.access_control_service import AccessControlService
from genai.system_admin.domain.access_control_domain import AccessControlDomain
from genai.system_admin.main import app

# 로그 DB 기록 중단
patch("genai.system_admin.common.util.system_admin_api_log.record_system_admin_api_log").start()
patch("genai.system_admin.common.util.system_admin_api_log.create_request_info").start()

# client = TestClient(app, root_path="/api/system-admin")
client = TestClient(app)

time_format = "%Y-%m-%dT%H:%M:%S.%f"


def mock_middleware_dispatch(*args, **kwargs):
    return args[1](args[0])


JWTParserMiddleware.dispatch = MagicMock(side_effect=mock_middleware_dispatch)


@pytest.fixture(scope="module")
def mock_get_user():
    def get_user() -> User:
        return User(
            id=UUID(int=3),
            tenant_id=1,
            name="tester",
            user_email="test@samsung.com",
            permission=[
                Permission.CREATE_ACCESS_CONTROL,
                Permission.READ_ACCESS_CONTROL,
                Permission.UPDATE_ACCESS_CONTROL,
                Permission.DELETE_ACCESS_CONTROL,
            ],
            access_token="test_token",
        )

    return get_user


@pytest.fixture(scope="module")
def mock_get_modify_user():
    def get_user() -> User:
        return User(
            id=UUID(int=10),
            tenant_id=1,
            name="tester_2",
            user_email="test_2@samsung.com",
            permission=[
                Permission.UPDATE_ACCESS_CONTROL,
            ],
            access_token="test_token",
        )

    return get_user


@pytest.fixture(scope="module")
def mock_get_no_permit_user():
    def get_user() -> User:
        return User(
            id=UUID(int=100),
            tenant_id=1,
            name="tester_3",
            user_email="test_3@samsung.com",
            permission=[],
            access_token="test_token",
        )

    return get_user


@pytest.fixture
def sample_access():
    return AccessControlDomain(
        access_id=1,
        access_title="테스트 접근 제어 제목",
        access_rule="192.168.0.0/24",
        is_active=True,
        created_at=datetime.now(UTC),
        modified_at=datetime.now(UTC),
        creator=UUID(int=3),
        modifier=UUID(int=3),
        creator_name="tester",
        modifier_name="tester",
    )


@pytest.fixture
def sample_accesses() -> list[AccessControlDomain]:
    return [
        AccessControlDomain(
            access_id=1,
            access_title="테스트 접근 제어 제목",
            access_rule="192.168.0.0/24",
            is_active=True,
            created_at=datetime.now(UTC),
            modified_at=datetime.now(UTC),
            creator=UUID(int=3),
            modifier=UUID(int=3),
            creator_name="tester",
            modifier_name="tester",
        ),
        AccessControlDomain(
            access_id=2,
            access_title="테스트 접근 제어 제목2",
            access_rule="10.0.0.0/8",
            is_active=False,
            created_at=datetime.now(UTC),
            modified_at=datetime.now(UTC),
            creator=UUID(int=10),
            modifier=UUID(int=10),
            creator_name="tester_2",
            modifier_name="tester_2",
        ),
    ]


def test_get_access_controls(sample_accesses, monkeypatch, mock_get_user):
    def mock_get_list(request, access_id, access_title, modified_at, pagination: PaginationParams):
        if pagination:
            return Page.of(sample_accesses, pagination.page, pagination.limit, len(sample_accesses))
        else:
            return sample_accesses

    monkeypatch.setattr(AccessControlService, "get_list", mock_get_list)
    app.dependency_overrides[get_user] = mock_get_user

    response = client.get("/api/system-admin/v1/access-controls")
    assert response.status_code == 200
    data = response.json()["data"]["items"]
    assert len(data) == 2
    access0 = data[0]
    assert access0["accessId"] == 1
    assert access0["accessTitle"] == "테스트 접근 제어 제목"
    assert access0["creatorName"] == "tester"
    assert access0["modifierName"] == "tester"
    access1 = data[1]
    assert access1["accessId"] == 2
    assert access1["accessTitle"] == "테스트 접근 제어 제목2"
    assert access1["creatorName"] == "tester_2"
    assert access1["modifierName"] == "tester_2"
    app.dependency_overrides.clear()


def test_get_access_controls_no_permit(sample_accesses, monkeypatch, mock_get_no_permit_user):
    def mock_get_list(request, access_id, access_title, modified_at, pagination):
        return sample_accesses

    monkeypatch.setattr(AccessControlService, "get_list", mock_get_list)
    app.dependency_overrides[get_user] = mock_get_no_permit_user

    response = client.get("/api/system-admin/v1/access-controls")
    assert response.status_code == 403
    error_response = response.json()
    assert error_response.get("error") == "Forbidden"
    assert error_response.get("errorCode") == "COMMON_ERROR_1"
    assert error_response.get("message") == "Access is denied"
    app.dependency_overrides.clear()


def test_get_access_controls_error(sample_accesses, monkeypatch, mock_get_user):
    def mock_get_list(request, access_id, access_title, modified_at, pagination):
        return sample_accesses

    monkeypatch.setattr(AccessControlService, "get_list", mock_get_list)
    app.dependency_overrides[get_user] = mock_get_user

    response = client.get(f"/api/system-admin/v1/access-controls?accessId={UUID(int=3)}&page=1&limit=10")
    assert response.status_code == 422
    error_response = response.json()
    assert error_response.get("error") == "Unprocessable Entity"
    assert error_response.get("errorCode") == "COMMON_ERROR_1"
    app.dependency_overrides.clear()


def test_create_access_control_success(monkeypatch, mock_get_user):
    create_access_id = 123

    def mock_create(request, access_domain: AccessControlDomain):
        new_access = access_domain.model_copy()
        new_access.access_id = create_access_id
        return new_access

    monkeypatch.setattr(AccessControlService, "create", mock_create)
    app.dependency_overrides[get_user] = mock_get_user

    request_data = {
        "accessTitle": "접근제어 생성 테스트",
        "accessRule": "172.16.0.0/12",
        "isActive": True,
    }
    response = client.post("/api/system-admin/v1/access-controls", json=request_data)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["accessId"] == create_access_id
    assert data["accessTitle"] == request_data["accessTitle"]
    assert data["accessRule"] == request_data["accessRule"]
    assert data["isActive"] == request_data["isActive"]
    assert data["creatorName"] == "tester"
    app.dependency_overrides.clear()


def test_create_access_control_fail(monkeypatch, mock_get_user):
    def mock_create(request, access_domain: AccessControlDomain):
        if access_domain.access_rule == "<invaide_ip>":
            raise BusinessException(error_code=ErrorCode.COMMON_ERROR_5, detail_message="Rule is invalide ICDR")

    monkeypatch.setattr(AccessControlService, "create", mock_create)
    app.dependency_overrides[get_user] = mock_get_user

    request_data = {"accessTitle": "접근제어 생성 테스트", "accessRule": "<invaide_ip>"}
    response = client.post("/api/system-admin/v1/access-controls", json=request_data)
    assert response.status_code == 400
    data = response.json()["message"]
    assert data == "Rule is invalide ICDR"
    app.dependency_overrides.clear()


def test_update_access_success(sample_accesses, monkeypatch, mock_get_modify_user):
    def mock_update(request, access_domain: AccessControlDomain):
        filtered_item: AccessControlDomain = [
            item for item in sample_accesses if access_domain.access_id == item.access_id
        ][0]
        filtered_item.access_title = access_domain.access_title
        filtered_item.access_rule = access_domain.access_rule
        filtered_item.is_active = access_domain.is_active
        filtered_item.modified_at = access_domain.modified_at
        filtered_item.modifier = access_domain.modifier
        filtered_item.modifier_name = access_domain.modifier_name
        return filtered_item

    monkeypatch.setattr(AccessControlService, "update", mock_update)
    app.dependency_overrides[get_user] = mock_get_modify_user

    access_id = 1
    request_data = {
        "accessTitle": "접근제어 수정 테스트",
        "accessRule": "172.16.0.0/12",
        "isActive": True,
    }
    response = client.put(f"/api/system-admin/v1/access-controls/access/{access_id}", json=request_data)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["accessId"] == access_id
    assert data["accessTitle"] == request_data["accessTitle"]
    assert data["accessRule"] == request_data["accessRule"]
    assert data["isActive"] == request_data["isActive"]
    app.dependency_overrides.clear()


def test_update_access_fail(monkeypatch, mock_get_modify_user):
    monkeypatch.setattr(AccessControlService, "update", None)
    app.dependency_overrides[get_user] = mock_get_modify_user

    response = client.put("/api/system-admin/v1/access-controls/access/2", json={})
    assert response.status_code == 422
    data = response.json()["message"]
    assert data == "accessTitle, Field required"
    app.dependency_overrides.clear()


def test_update_access_fail_2(sample_accesses, monkeypatch, mock_get_modify_user):
    def mock_update(request, access_domain):
        filtered_item = [item for item in sample_accesses if access_domain.access_id == item.access_id]
        if len(filtered_item) <= 0:
            raise BusinessException(error_code=ErrorCode.COMMON_ERROR_4, detail_message="The id does not exist")
        return filtered_item[0]

    monkeypatch.setattr(AccessControlService, "update", mock_update)
    app.dependency_overrides[get_user] = mock_get_modify_user

    request_data = {
        "accessTitle": "접근제어 수정 테스트",
        "accessRule": "172.16.0.0/12",
        "isActive": True,
    }
    response = client.put("/api/system-admin/v1/access-controls/access/9999", json=request_data)
    assert response.status_code == 404
    data = response.json()["message"]
    assert data == "The id does not exist"
    app.dependency_overrides.clear()


def test_delete_access_success(monkeypatch, mock_get_user):
    def mock_delete(request, access_id: int) -> str:
        if access_id == 1:
            return f"success: [{access_id}]"
        else:
            raise ServerException(
                ErrorCode.COMMON_ERROR_4,
                f"The AccessControl [{access_id}] is already deleted",
            )

    monkeypatch.setattr(AccessControlService, "delete", mock_delete)
    app.dependency_overrides[get_user] = mock_get_user

    response = client.delete("/api/system-admin/v1/access-controls/access/1")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["message"] == "success: [1]"
    app.dependency_overrides.clear()


def test_delete_access_fail(monkeypatch, mock_get_user):
    def mock_delete(request, access_id: int) -> str:
        if access_id == 1:
            return f"success: [{access_id}]"
        else:
            raise ServerException(
                ErrorCode.COMMON_ERROR_4,
                f"The AccessControl [{access_id}] is already deleted",
            )

    monkeypatch.setattr(AccessControlService, "delete", mock_delete)
    app.dependency_overrides[get_user] = mock_get_user

    response = client.delete("/api/system-admin/v1/access-controls/access/2")
    assert response.status_code == 404
    data = response.json()
    assert data["message"] == "The AccessControl [2] is already deleted"
    app.dependency_overrides.clear()


def test_get_access_by_id(sample_access, monkeypatch, mock_get_user):
    def mock_get_by_id(request, access_id: int):
        return sample_access if access_id == 1 else None

    monkeypatch.setattr(AccessControlService, "get_by_id", mock_get_by_id)
    app.dependency_overrides[get_user] = mock_get_user

    response = client.get("/api/system-admin/v1/access-controls/access/1")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["accessId"] == 1
    assert data["accessTitle"] == "테스트 접근 제어 제목"
    assert data["accessRule"] == "192.168.0.0/24"
    assert data["isActive"]
    app.dependency_overrides.clear()


def test_check_validate_access(sample_access, monkeypatch, mock_get_user):
    def mock_get_by_id(request, access_id: int):
        return sample_access if access_id == 1 else None

    def mock_get_by_rule(request, rule: str):
        return sample_access if rule == "192.168.0.0/24" else None

    monkeypatch.setattr(AccessControlService, "get_by_id", mock_get_by_id)
    app.dependency_overrides[get_user] = mock_get_user
    monkeypatch.setattr(AccessControlService, "get_by_rule", mock_get_by_rule)
    app.dependency_overrides[get_user] = mock_get_user

    rule = parse.quote("192.168.0.0/24", safe="")
    response = client.get(f"/api/system-admin/v1/access-controls/validate?accessRule={rule}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert not data["isValidate"]

    rule = parse.quote("10.0.0.0/8", safe="")
    response = client.get(f"/api/system-admin/v1/access-controls/validate?accessRule={rule}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["isValidate"]

    rule = parse.quote("10.0.0.0/8", safe="")
    response = client.get(f"/api/system-admin/v1/access-controls/validate?subject=update&accessId=1&accessRule={rule}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["isValidate"]

    response = client.get("/api/system-admin/v1/access-controls/validate?subject=delete&accessId=2")
    assert response.status_code == 200
    data = response.json()["data"]
    assert not data["isValidate"]

    app.dependency_overrides.clear()


if __name__ == "__main__":
    # for vanilla unittest
    # unittest.main()
    # for all tests with pytest
    pytest.main(["-s", "-v", __file__])
    # for a specific pytest function
    # pytest.main(["-s", "-v", __file__ + "::test_specific"])
