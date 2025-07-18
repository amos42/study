import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from keycloak import KeycloakAdmin, KeycloakOpenID
from keycloak.exceptions import KeycloakError
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import Query
# import requests


# .env 파일에서 환경 변수 로드
load_dotenv()

# Keycloak 설정
KEYCLOAK_SERVER_URL = os.getenv("KEYCLOAK_SERVER_URL")
KEYCLOAK_REALM_NAME = os.getenv("KEYCLOAK_REALM_NAME")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID")
KEYCLOAK_CLIENT_UUID = os.getenv("KEYCLOAK_CLIENT_UUID")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET")
KEYCLOAK_ADMIN_USER = os.getenv("KEYCLOAK_ADMIN_USER")
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD")
KEYCLOAK_FRONTEND_CLIENT_ID = os.getenv("KEYCLOAK_FRONTEND_CLIENT_ID")

# FastAPI 앱 생성
app = FastAPI()

# CORS 설정
origins = [
    "http://localhost:3000",  # React 앱의 주소
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

keycloak_openid = KeycloakOpenID(
    server_url=KEYCLOAK_SERVER_URL,
    client_id=KEYCLOAK_CLIENT_ID,
    realm_name=KEYCLOAK_REALM_NAME,
)

# OAuth2 스킴 정의
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

keycloak_admin_data: KeycloakAdmin | None = None

class UserInfo(BaseModel):
    user_info: dict
    token: str

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInfo:
    """프론트엔드에서 받은 Keycloak 토큰을 검증하고 사용자 정보를 반환합니다."""
    try:
        user_info = keycloak_openid.userinfo(token)
        return UserInfo(user_info=user_info, token=token)
    except KeycloakError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

def get_keycloak_admin(authorization: str | None = None) -> KeycloakAdmin:
    """Keycloak Admin 클라이언트를 생성하고 반환합니다."""
    global keycloak_admin_data
    try:
        if keycloak_admin_data:
            return keycloak_admin_data
        keycloak_admin_data = KeycloakAdmin(
            server_url=KEYCLOAK_SERVER_URL,
            username=KEYCLOAK_ADMIN_USER,
            password=KEYCLOAK_ADMIN_PASSWORD,
            realm_name=KEYCLOAK_REALM_NAME,
            client_id=KEYCLOAK_CLIENT_ID,
            client_secret_key=KEYCLOAK_CLIENT_SECRET,
            token={"access_token":authorization, "expires_in": 0},
            verify=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Keycloak 연결 실패: {str(e)}")

    return keycloak_admin_data

class UserAttributes(BaseModel):
    email: str
    enabled: bool
    attributes: dict

@app.get("/api/users")
async def get_users(
    current_user = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """모든 사용자의 목록을 페이지네이션하여 반환합니다."""
    keycloak_admin = get_keycloak_admin(current_user.token)
    try:
        start = (page - 1) * page_size
        users = keycloak_admin.get_users({"first": start, "max": page_size})
        total_users = keycloak_admin.users_count({})
        # sessions0 = keycloak_admin.get_client_sessions_stats()
        # print(sessions0)
        sessions = keycloak_admin.get_client_all_sessions(client_id=KEYCLOAK_CLIENT_UUID)
        active_user_ids = set(session['userId'] for session in sessions)
        active_users = len(active_user_ids)

        return {
            "total_users": total_users,
            "active_users": active_users,
            "page": page,
            "page_size": page_size,
            "users": [{"id": u["id"], "username": u.get("username"), "email": u.get("email"), "enabled": u.get("enabled", True), "attributes": u.get("attributes", {})} for u in users]
        }
    except KeycloakError as e:
        raise HTTPException(status_code=e.response_code, detail=str(e))

@app.get("/api/users/{user_id}")
async def get_user_details(user_id: str, current_user = Depends(get_current_user)):
    """특정 사용자의 상세 정보를 반환합니다."""
    keycloak_admin = get_keycloak_admin(current_user.token)
    try:
        user = keycloak_admin.get_user(user_id)
        return user
    except KeycloakError as e:
        raise HTTPException(status_code=e.response_code, detail=str(e))

@app.put("/api/users/{user_id}")
async def update_user_attributes(user_id: str, user_attributes: UserAttributes, current_user = Depends(get_current_user)):
    """특정 사용자의 속성을 업데이트합니다."""
    keycloak_admin = get_keycloak_admin(current_user.token)
    try:
        # 사용자 정보 페이로드 구성
        payload = {"email": user_attributes.email, "enabled": user_attributes.enabled, "attributes": user_attributes.attributes}
        keycloak_admin.update_user(user_id=user_id, payload=payload)
        return {"message": f"사용자 {user_id}의 속성이 성공적으로 업데이트되었습니다."}
    except KeycloakError as e:
        raise HTTPException(status_code=e.response_code, detail=str(e))

@app.get("/api/users/{user_id}/login-history")
async def get_user_login_history(
    user_id: str,
    current_user = Depends(get_current_user),
    start: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """
    특정 사용자의 로그인 이력을 페이지네이션하여 반환합니다.
    (Keycloak 세션 정보를 기반으로 하며, 실제 로그인 이력과는 다를 수 있습니다.)
    """
    try:
        keycloak_admin = get_keycloak_admin(current_user.token)
        events = keycloak_admin.get_events({"user":user_id, "client":KEYCLOAK_FRONTEND_CLIENT_ID, "type":["LOGIN","LOGOUT","LOGIN_ERROR"], "direction":"desc", "first": start, "max": page_size})
        # response = requests.get(f"http://localhost:8080/admin/realms/master/events?user={user_id}&type=LOGIN&type=LOGOUT&type=LOGIN_ERROR&first={start}&max={page_size}",
        #                         headers={"Authorization": f"Bearer {current_user.token}"})
        # events = response.json()

        return {
            "start": start,
            "page_size": page_size,
            "history": events
        }
    except KeycloakError as e:
        raise HTTPException(status_code=e.response_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @app.post("/logs")
# async def receive_logs(log: any):
#     """Receives JBoss logs via POST request and prints them to the console."""
#     print(f"Received log: {log}")
#     return {"status": "log received"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
