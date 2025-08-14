from fastapi import APIRouter, Depends, Header
from typing import Any, Dict
from auth.auth import get_user_from_token
import requests

router = APIRouter()

@router.get("/")
def read_apps(user_info: Dict = Depends(get_user_from_token), authorization: str = Header(None)) -> Any:  # noqa: F821
    headers = {
        "Content-Type": "application/json",
        "Authorization": authorization
    }
    response = requests.request(
        "get", "http://localhost:8080/realms/master/account/applications",
        headers=headers
    )
    # print(response.content)
    return response.json()
