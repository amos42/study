import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app, get_keycloak_admin, get_current_user

# filepath: d:\study\study\keycloak_example\userman\backend\test_main.py

client = TestClient(app)

@pytest.fixture
def mock_keycloak_admin():
    with patch("main.get_keycloak_admin") as mock_admin:
        mock_instance = MagicMock()
        mock_admin.return_value = mock_instance
        yield mock_instance

# @pytest.fixture
# def mock_current_user():
#     with patch("main.get_current_user") as mock_user:
#         mock_user.return_value = {"user_info": {"preferred_username": "test_user"}, "token": "mock_token"}
#         yield mock_user

@pytest.fixture
def mock_oauth2_scheme():
    with patch("main.oauth2_scheme") as mock_token:
        mock_token.return_value = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJMNHI2aDVtNWxmdHdNSGREODY0T2tCN2UzTEwzLXp5Mzk4SHdpM1lyWXU0In0.eyJleHAiOjE3NTU4NjA1MDAsImlhdCI6MTc1NTg2MDQ0MCwianRpIjoib25sdGFjOmExMThlZWQxLTAzZjItOWYyYy04NWYxLWI3MGYwZWFhZWU3MyIsImlzcyI6Imh0dHA6Ly9sb2NhbGhvc3Q6ODA4MC9yZWFsbXMvbWFzdGVyIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoic2VjdXJpdHktYWRtaW4tY29uc29sZSIsInNpZCI6ImUzODc4MTRkLWRhNzEtNDNmYi1hNTFkLTFjN2Y5YjE3ZmRiMiIsInNjb3BlIjoib3BlbmlkIGVtYWlsIHByb2ZpbGUifQ.kpFctoZ5VfCFdBOPlVMyJtycYOhx8ypKzUUg-ZwdUoWjdHYZ8eltAAwgoiOS9i_APKvCjf7NVh8MfPaDnssbnlxCxoHUQNB6Oq-SELsPSZF9uEv3mQ__EpujbECqhs1mxHBeyjQlE-4KgvNCFNFTCLnWYkl42ZgVtNyqjc892tcMZi4Hj8jbeg_6sNZf_bAvmHfKyy1NwI5eTQjOXUQOT_M9EPbBAnhaW9YoNQ1jS5sX6ccBvKgtSRM2o2u75vcbRaGvOfMK39UhR3dK0IYTSo8Hix7YffflixpWSMVvS4PUnq4GglngPG-dZ0tM00K9pRdnUjRVYg3j7gqW_Wr4Pg"
        yield mock_token

def test_get_users(mock_keycloak_admin, mock_oauth2_scheme):
    mock_keycloak_admin.get_users.return_value = [{"id": "1", "username": "user1", "email": "user1@example.com"}]
    mock_keycloak_admin.users_count.return_value = 1
    mock_keycloak_admin.get_client_all_sessions.return_value = [{"userId": "1"}]

    response = client.get("/api/users?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json() == {
        "total_users": 1,
        "active_users": 1,
        "page": 1,
        "page_size": 10,
        "users": [{"id": "1", "username": "user1", "email": "user1@example.com", "enabled": True, "attributes": {}}]
    }

def test_get_user_details(mock_keycloak_admin, mock_oauth2_scheme):
    mock_keycloak_admin.get_user.return_value = {"id": "1", "username": "user1", "email": "user1@example.com"}

    response = client.get("/api/users/1")
    assert response.status_code == 200
    assert response.json() == {"id": "1", "username": "user1", "email": "user1@example.com"}

def test_update_user_attributes(mock_keycloak_admin, mock_oauth2_scheme):
    response = client.put(
        "/api/users/1",
        json={"email": "user1@example.com", "enabled": True, "attributes": {"key": "value"}}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "사용자 1의 속성이 성공적으로 업데이트되었습니다."}

def test_update_user_tenants(mock_keycloak_admin, mock_oauth2_scheme):
    mock_keycloak_admin.get_user.return_value = {"attributes": {"tenant_id": ["tenant1"]}}

    response = client.put(
        "/api/users/1/tenant",
        json=["tenant1", "tenant2"]
    )
    assert response.status_code == 200
    assert response.json() == {"message": "사용자 1의 속성이 성공적으로 업데이트되었습니다."}

def test_update_user_tenant_id(mock_keycloak_admin, mock_oauth2_scheme):
    mock_keycloak_admin.get_user.return_value = {"attributes": {"tenant_id": "tenant1"}}

    response = client.put("/api/users/1/tenant/tenant2")
    assert response.status_code == 200
    assert response.json() == {"message": "사용자 1의 속성이 성공적으로 업데이트되었습니다."}

def test_get_user_login_history(mock_keycloak_admin, mock_oauth2_scheme):
    mock_keycloak_admin.get_events.return_value = [{"type": "LOGIN", "details": "Login successful"}]

    response = client.get("/api/users/1/login-history?start=1&page_size=10")
    assert response.status_code == 200
    assert response.json() == {
        "start": 1,
        "page_size": 10,
        "history": [{"type": "LOGIN", "details": "Login successful"}]
    }