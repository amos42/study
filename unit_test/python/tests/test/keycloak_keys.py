import uuid
from datetime import datetime
from datetime import timedelta
from uuid import UUID

import jwt
from fastapi.security import HTTPAuthorizationCredentials

from genai.base.constants.permission import Permission

# 테스트용 private_key/public_key
# public_key는 genai.base.common.auth 모듈에 KEYCLOAK_PUBLICKEY 환경변수를 통해 전달

# https://cryptotools.net/rsagen
keycloak_private_key_raw = """MIIEowIBAAKCAQEAu+Wu8femdc7S8D03DHvxQ/TPdFJE0c6gZiqEHG/LzehoMlJ7
bIjsfXNt6tmFdbpNkaMJIY//hEJTVAZqv1jTYghjmduP+SwVr7vb0dnEunrPCHT8
69cSykTP/otGo4+sG7a4GwSn3isWDnoYdTUUi02uUeyhiRLOozOWutmgGEFGx9TO
rTFmVMnOdcPX9zcMOffeY/kPtJ+Kowc+QEumv68pjZYWpL3dka325tLINFJ3a4/f
p3Z7gqUxqxWFREgAlkm7EYpLVjqiDI9iAEZOaDeX/IfJPbcLBeTz+qixpZ/1l5nO
8pEra+OUvWju8TLy9W9qM4ckpNX8hpfADhNtMQIDAQABAoIBADnEmu3PmwD7ToUH
/QW8kWe4O5Piuz/aDBx9E9L+WCV9P5PBIiszSaokM/YRXGPenHybKHKGKCPMlHvv
4R/lOlAYji6+f1w3Po+h7SpujnpayY4rEZucqy0+zMfQoC4nPN3kZmQAIXA/xO88
gIqAgEl335FWdC+FdbxdXwkhYYQy/Q4OPSqckSVRsgO61Ahl1v8e8zrgpJ/jzpVb
8erF6MxqQiehtM0PlrEZgnNF8GyHeb+0avtz4JSTF48ACyFSbGfDr3H1CU2nx6I7
vh6AjoeZVcHYF/BN4XnM3YMcuEuA0gSPpG2g0FjGpWqCPMm1MUHPBDz3qhZQg/Dg
T3VQKHUCgYEA/9vw3/aFHhVZc2A1YKF+HUrhOQhPpGe911Q31zP4FFv+hHX+8rU4
6QXJkU2HlS3uzwJVHTQYnRpFRjZlK0al1YSSoBy/aweyB7zJ2YfDBETZwqsgGxES
kinCKJt9AstivoWLCLjOXNqJ9OJD6VqKhk8aZ7acxhzRkba12k5C9ZcCgYEAvAAq
E2vURN6gTTEdzFSrYmnPYI+QkuVnYUrw5ywkkUepS0EJeGQZQVQtOsjYS8gfJah2
P/5qbxcnUNShyh+c/OiF+9hqUzFCai7/72GFMet2+P4Iz/PtmBs9MTFTqVxnZyfJ
xY+/ZvX9Pc6SGyzzHp0Nvq4CnEEQHZjAL5j3XHcCgYBlvUOPCyvrxnmHU15mSlEn
vLrKPu/MZCQtF6QMwvGGxv3yFimGwWEb5907FiUvwNARKNBHiIuxDN03CjI4fyM6
QDk9ybCkEq9MPFnXUhDOBcLBkeJ2YNeNn2VBWHLhRZbCQ8ABe9szOQNaiQ6QIByt
Q48wZoD4lkUPOCQf5rbhiQKBgDj3x8g4zYrM90BM2N247nIU5A07k7CfqTL3NYan
frEzSN6P56G+m1SLgGUmxTw5eQ69PI/ptTDSkExTEm+gIr8Uar1E9/sbmyd39IAC
Sg01b8jFmcACB4YnAuTsMJDKel7s1Jx0EajOc52OAgIQHd+x8Z9NNWdJ4+tEBUCn
FpXDAoGBAOkS6Fdm/p0wq8QQeyNpeYNWOYNV9nFYzZ67qk6s1tvgSs88J5rFutV8
CHSNt/DRzqrfkIQGzihQnjCGuo+URLQunErIhJQey8x8MiVvWUcEZaqeYNZZMno3
nh+3SVuda/jTEdUIEBPtgdXreNTZ9lcQFMca18p3Kmed4wPiNnih"""

keycloak_private_key = f"-----BEGIN RSA PRIVATE KEY-----\n{keycloak_private_key_raw}\n-----END RSA PRIVATE KEY-----"

keycloak_public_key_raw = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAu+Wu8femdc7S8D03DHvxQ/TPdFJE0c6gZiqEHG/LzehoMlJ7bIjsfXNt6tmFdbpNkaMJIY//hEJTVAZqv1jTYghjmduP+SwVr7vb0dnEunrPCHT869cSykTP/otGo4+sG7a4GwSn3isWDnoYdTUUi02uUeyhiRLOozOWutmgGEFGx9TOrTFmVMnOdcPX9zcMOffeY/kPtJ+Kowc+QEumv68pjZYWpL3dka325tLINFJ3a4/fp3Z7gqUxqxWFREgAlkm7EYpLVjqiDI9iAEZOaDeX/IfJPbcLBeTz+qixpZ/1l5nO8pEra+OUvWju8TLy9W9qM4ckpNX8hpfADhNtMQIDAQAB"

keycloak_public_key = f"-----BEGIN PUBLIC KEY-----\n{keycloak_public_key_raw}\n-----END PUBLIC KEY-----"


def make_user_token(
    user_id: UUID,
    user_name: str,
    user_email: str,
    company_code: str,
    department_code: str,
    department_name: str,
    tenant_id: int,
    tenant_code: str,
    tenants: list[int],
    permissions: list[Permission] | None = None,
) -> HTTPAuthorizationCredentials:
    payload = {
        "iat": datetime.now(),
        "exp": datetime.now() + timedelta(hours=1),
        "jti": f"onltac:{uuid.uuid1()}",
        "iss": "http://localhost:8080/realms/master",
        "aud": "http://localhost:3000/",
        "typ": "Bearer",
        "sid": str(uuid.uuid1()),
        "scope": "openid profile email",
        "azp": "security-admin-console",
        "id": str(user_id),
        "name": user_name,
        "client_uuid": str(UUID(int=10000)),
        "user_name": user_name,
        "user_email": user_email,
        "company_code": company_code,
        "department_code": department_code,
        "department_name": department_name,
        "tenant_id": tenant_id,
        "tenant_code": tenant_code,
        "tenants": tenants,
        "permission": permissions,
        # "access_token": "test_token",
    }
    token = jwt.encode(payload, keycloak_private_key, algorithm="RS256")
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
