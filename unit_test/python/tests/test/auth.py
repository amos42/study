import asyncio
import logging
from functools import wraps
from typing import Any
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from genai.base.common.config import get_settings
from genai.base.common.exception import ServerException
from genai.base.common.logger_support import get_logger
from genai.base.constants.error_code import ErrorCode
from genai.base.constants.permission import Permission

settings = get_settings()

oauth_scheme = HTTPBearer()

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)

HTTP_EXCEPTION_INVALID_BEARER_TOKEN = "Invalid bearer token"
HTTP_EXCEPTION_INVALID_CLIENT_ACCESS_TOKEN = "Invalid client-access token"
MESSAGE_API_PERMISSION_CHECK = "API Permission check was passed"
MESSAGE_ACCESS_DENIED = "Access is denied"
SCHEME_AUTHORIZATION_BEARER = "Bearer"


# Authentication support


class User(BaseModel):
    id: UUID | int | None
    tenant_id: int
    tenant_code: str | None = None
    tenants: list[int] | None = None
    user_email: str
    role: list[str] | None = None
    permission: list[str]
    access_token: str
    name: str | None = None
    aud: str | list[str] | None = None
    client_id: str | None = None
    client_uuid: str | None = None
    department_code: str | None = None
    department_name: str | None = None
    company_code: str | None = None

    def get(self, key: str, default=None):
        return self.model_dump().get(key, default)


def _split_bearer_authorization(authorization: str):
    return authorization.split(f"{SCHEME_AUTHORIZATION_BEARER} ")


def _is_bearer_authorization(authorization: str) -> bool:
    return authorization.startswith(f"{SCHEME_AUTHORIZATION_BEARER} ")


async def get_user(token: HTTPAuthorizationCredentials = Depends(oauth_scheme)):
    return _get_user_from_credentials(token.credentials)


def get_user_from_token(token: str) -> User | dict:
    if not token:
        logger.info("Access Token does not exist")
        return {}

    try:
        return _get_user_from_credentials(token)
    except HTTPException as e:
        logger.info(f"Decoded token is invalid: {e}")
        return {}


def get_user_from_token_without_request(token: str) -> User | dict:
    if not token:
        logger.info("Access Token does not exist")
        return {}

    try:
        # 추후 _get_user_from_credentials 에 request: Request 파라미터 추가되면 변경 필요
        # return _get_user_from_credentials(request=None, token_credentials=token)
        return _get_user_from_credentials(token_credentials=token)
    except HTTPException as e:
        logger.info(f"Decoded token is invalid: {e}")
        return {}


def _get_user_from_credentials(token_credentials: str):
    try:
        # new token test
        token_object = decode_jwt_token(token_credentials)

        impersonation_user = {}
        # if request:
        #     impersonation_user_email = request.headers.get("x-generative-ai-user-email")
        #     b64_encoded_user = request.headers.get("x-generative-ai-user")
        #     logger.info(f"impersonation_user_email : {impersonation_user_email}")
        # if impersonation_user_email and b64_encoded_user:
        #     b64_decoded_user = base64.b64decode(b64_encoded_user).decode('utf-8')
        #     user = unquote(b64_decoded_user)
        #     impersonation_user = json.loads(user)
        #     logger.info(f"x-generative-ai-user : {(impersonation_user)}")

        if token_object.get("iss"):
            # new token test
            logger.info("use new token")
            logger.debug(f"token_object: {token_object}")

            # Client credentials grant does not contain user information
            aud = token_object.get("aud", None)

            tenant_id: int = token_object.get("tenant_id") or -1
            permission_raw = token_object.get("permission")
            permission_prefix = "perm_"
            permission = [s[len(permission_prefix) :] if s.startswith(permission_prefix) else s for s in permission_raw]
            user: User = User(
                id=impersonation_user.get("id") or token_object.get("id"),
                tenant_id=tenant_id,
                tenant_code=token_object.get("tenant_code"),
                tenants=token_object.get("tenants"),
                user_email=impersonation_user.get("userEmail") or token_object.get("user_email") or "",
                permission=permission,
                name=impersonation_user.get("userName") or token_object.get("user_name"),
                access_token=token_credentials,
                aud=aud,
                client_id=token_object.get("azp"),
                client_uuid=token_object.get("client_uuid"),
                department_code=impersonation_user.get("departmentCode") or token_object.get("department_code"),
                company_code=impersonation_user.get("companyCode") or token_object.get("company_code"),
                department_name=impersonation_user.get("departmentName") or token_object.get("department_name"),
            )
            return user
        else:
            # old token
            logger.info("use old token")
            user: User = User(
                id=token_object.get("id"),
                tenant_id=token_object.get("tenantId") or -1,
                tenant_code=token_object.get("tenantCode"),
                user_email=token_object.get("user_email"),
                permission=token_object.get("permission"),
                name=token_object.get("user_name"),
                access_token=token_credentials,
                client_id=token_object.get("client_id"),
                client_uuid=token_object.get("client_uuid"),
                department_code=token_object.get("department_code"),
                company_code=token_object.get("company_code"),
            )
            return user

    except Exception as e:
        logger.exception("Exception", exc_info=e)
        raise e


class Client(BaseModel):
    id: UUID
    client_id: str
    allowed_origins: list[str] | None = None
    scope: str | None = None
    client_host: str | None = None
    permission: list[str] | None = None
    preferred_username: str | None = None


async def get_client(token: HTTPAuthorizationCredentials = Depends(oauth_scheme)):
    return _get_client_from_credentials(token.credentials)


def _get_client_from_credentials(token_credentials: str):
    try:
        token_object = decode_jwt_token(token_credentials)
        logger.info(f"token_object: {token_object}")

        client: Client = Client(
            id=token_object.get("id"),
            client_id=token_object.get("client_id"),  # or token_object.get("azp"),
            allowed_origins=token_object.get("allowed_origins"),
            scope=token_object.get("scope"),
            client_host=token_object.get("clientHost"),
            permission=token_object.get("permission"),
            preferred_username=token_object.get("preferred_username"),
        )
        return client
    except Exception as e:
        # logger.exception("Exception", exc_info=e)
        raise HTTPException(status_code=401, detail=HTTP_EXCEPTION_INVALID_CLIENT_ACCESS_TOKEN) from e


def get_from_token(token: dict, field: str) -> str:
    try:
        return token.get(field)
    except jwt.InvalidTokenError as err:
        raise HTTPException(status_code=401, detail=f"Invalid JWT token : {field}") from err


def get_bearer_token(request: Request) -> str:
    authorization_header = request.headers.get("Authorization")
    if not authorization_header or not _is_bearer_authorization(authorization_header):
        raise HTTPException(status_code=401, detail=HTTP_EXCEPTION_INVALID_BEARER_TOKEN)

    split_header = _split_bearer_authorization(authorization_header)
    if len(split_header) != 2:
        raise HTTPException(status_code=401, detail=HTTP_EXCEPTION_INVALID_BEARER_TOKEN)

    return split_header[1]


def _get_bearer_token_from_authorization(authorization: str) -> str:
    if not _is_bearer_authorization(authorization):
        raise HTTPException(status_code=401, detail=HTTP_EXCEPTION_INVALID_BEARER_TOKEN)

    split_header = _split_bearer_authorization(authorization)
    if len(split_header) != 2:
        raise HTTPException(status_code=401, detail=HTTP_EXCEPTION_INVALID_BEARER_TOKEN)

    return split_header[1]


def get_token_from_authorization(authorization: str) -> dict:
    if not authorization:
        logger.info("Authorization does not exist")
        return None

    try:
        return _get_bearer_token_from_authorization(authorization)
    except HTTPException as e:
        logger.info(f"Request token is invalid: {e}")
        return None


def decode_jwt_token(encoded_token: str) -> dict:
    try:
        secret_key = settings.jwt_secret
        decoded_token = jwt.decode(encoded_token, secret_key, algorithms=["HS256"])
        return decoded_token
    except Exception:
        try:
            logger.info("try new token decode")
            public_key = f"-----BEGIN PUBLIC KEY-----\n{settings.keycloak_publickey}\n-----END PUBLIC KEY-----"
            decoded_token = jwt.decode(encoded_token, public_key, algorithms=["RS256"], options={"verify_aud": False})
            return decoded_token
        except jwt.ExpiredSignatureError as err:
            raise HTTPException(status_code=401, detail="Signature has expired") from err
        except jwt.InvalidTokenError as err:
            raise HTTPException(status_code=401, detail="Invalid JWT token when decoding") from err


def permit(*allowed_permissions: Permission):
    def wrapper(func):
        @wraps(func)
        async def async_decorated(*args, **kwargs):
            _check_permissions(*allowed_permissions, **kwargs)
            logger.debug(MESSAGE_API_PERMISSION_CHECK)
            result = await func(*args, **kwargs)
            return result

        @wraps(func)
        def sync_decorated(*args, **kwargs):
            _check_permissions(*allowed_permissions, **kwargs)
            logger.debug(MESSAGE_API_PERMISSION_CHECK)
            result = func(*args, **kwargs)
            return result

        if asyncio.iscoroutinefunction(func):
            return async_decorated
        else:
            return sync_decorated

    return wrapper


def permit_sync(*allowed_permissions: Permission):
    def wrapper(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            if asyncio.iscoroutinefunction(func):
                raise ServerException(
                    ErrorCode.COMMON_ERROR_1,
                    "func is not sync.",
                )
            _check_permissions(*allowed_permissions, **kwargs)
            logger.info(MESSAGE_API_PERMISSION_CHECK)
            return func(*args, **kwargs)

        return decorated

    return wrapper


# Authorization support


def _check_permissions(*allowed_permissions: Permission, **kwargs: Any):
    _user: User | None = None
    for v in kwargs.values():
        if isinstance(v, User):
            _user = v
            break

    if not _user or not hasattr(_user, "permission"):
        logger.warning("No user")
        raise HTTPException(status_code=403, detail=MESSAGE_ACCESS_DENIED)

    if not hasattr(_user, "permission"):
        logger.warning("No permission")
        raise HTTPException(status_code=403, detail=MESSAGE_ACCESS_DENIED)

    if hasattr(_user, "id"):
        logger.info("user.id:" + str(_user.id))
    logger.debug("user.permission:" + str(_user.permission))

    allowed_permission_values = list(map(lambda p: p.value, allowed_permissions))
    if not any(permission in allowed_permission_values for permission in _user.permission):
        logger.warning("Insufficient permission")
        raise HTTPException(status_code=403, detail=MESSAGE_ACCESS_DENIED)
