from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer
from keycloak.keycloak_openid import KeycloakOpenID
from typing import Optional, Dict

from pydantic import BaseModel

router = APIRouter()

# idp = FastAPIKeycloak(
#     server_url="http://localhost:8080/",  # Keycloak 서버 URL
#     client_id="test",         # Keycloak 클라이언트 ID
#     client_secret="8QwyK9v2Mt5oVd7wQSjOywqmKZUOCUHg", # Keycloak 클라이언트 Secret
#     admin_client_id="admin-cli", # 관리자 클라이언트 ID (일반적으로 admin-cli 사용)
#     admin_client_secret="Iwh9tJ6g1wWPIV1njhUNZCI0cVnkYzqG", # 관리자 클라이언트 Secret
#     realm="master",            # Keycloak Realms
#     callback_uri="http://localhost:8000/callback" # 로그인 후 콜백 URL,
# )

keycloak_openid = KeycloakOpenID(
    server_url="http://localhost:8080/",
    client_id="test-be",
    realm_name="master",
    client_secret_key="OTP3HWboqvt9AymQEQtrYmXW4mXHVioh"
)

#oauth_scheme = OAuth2PasswordBearer(tokenUrl="token")
oauth_scheme = HTTPBearer()

# 주의: 어플리케이션 시작시 init()이 호출되어야 합니다.
#@router.on_event("startup")
#async def startup_event():
#    await idp.init()

class User(BaseModel):
    id: str | None = None
    sub: UUID | None = None
    email_verified: bool | None = None
    preferred_username: str | None = None

# Keycloak에서 토큰을 검증하는 함수
async def get_user_from_token(token: str = Depends(oauth_scheme)) -> User:
    try:        
        # 토큰 검증
        # info = keycloak_openid.decode_token(token, keycloak_openid.certs(), options={'verify_signature': True, 'verify_aud': True, 'exp': True})
        info = keycloak_openid.userinfo(token.credentials)
        # print(info)
        return User(**info)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid Token: {e}", headers={"WWW-Authenticate": "Bearer"})
