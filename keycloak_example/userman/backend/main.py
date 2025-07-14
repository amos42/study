import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from keycloak import KeycloakAdmin, KeycloakOpenID
from keycloak.exceptions import KeycloakError
from dotenv import load_dotenv
from pydantic import BaseModel

# .env 파일에서 환경 변수 로드
load_dotenv()

# Keycloak 설정
KEYCLOAK_SERVER_URL = os.getenv("KEYCLOAK_SERVER_URL")
KEYCLOAK_REALM_NAME = os.getenv("KEYCLOAK_REALM_NAME")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID")
KEYCLOAK_ADMIN_USER = os.getenv("KEYCLOAK_ADMIN_USER")
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD")

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

def get_keycloak_admin(authorization: str | None = None):
    """Keycloak Admin 클라이언트를 생성하고 반환합니다."""
    try:
        keycloak_admin = KeycloakAdmin(
            server_url=KEYCLOAK_SERVER_URL,
            username=KEYCLOAK_ADMIN_USER,
            password=KEYCLOAK_ADMIN_PASSWORD,
            realm_name=KEYCLOAK_REALM_NAME,
            client_id=KEYCLOAK_CLIENT_ID,
            token={"access_token":authorization, "expires_in": 0},
            verify=True
        )
        return keycloak_admin
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Keycloak 연결 실패: {str(e)}")

class UserAttributes(BaseModel):
    email: str
    attributes: dict

@app.get("/api/users")
async def get_users(current_user = Depends(get_current_user)):
    """모든 사용자의 목록을 반환합니다."""
    keycloak_admin = get_keycloak_admin(current_user.token)
    try:
        users = keycloak_admin.get_users({})
        # 필요한 정보만 추출하여 반환 (id, username, email, attributes)
        return [{"id": u["id"], "username": u.get("username"), "email": u.get("email"), "attributes": u.get("attributes", {})} for u in users]
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
        payload = {"email": user_attributes.email, "attributes": user_attributes.attributes}
        keycloak_admin.update_user(user_id=user_id, payload=payload)
        return {"message": f"사용자 {user_id}의 속성이 성공적으로 업데이트되었습니다."}
    except KeycloakError as e:
        raise HTTPException(status_code=e.response_code, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
