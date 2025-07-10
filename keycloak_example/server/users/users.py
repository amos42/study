from uuid import UUID
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from auth.auth import get_user_from_token
import requests

class User(BaseModel):
    id: int
    sub: UUID | None = None
    email_verified: bool | None = None
    preferred_username: str | None = None
    company: str | None = None

router = APIRouter()

@router.get("/")
def read_users(user_info: User = Depends(get_user_from_token)) -> list[User]:
    return [user_info]

@router.post("/")
def create_user(name: str, email: str, user_info: User = Depends(get_user_from_token)):
    return {"message": "사용자 생성", "name": name, "email": email, "created_by": user_info.username}

@router.get("/{user_id}")
def read_user(user_id: int, user_info: User = Depends(get_user_from_token), authorization: str = Header(None)) -> User:
    headers = {
        "Content-Type": "application/json",
        "Authorization": authorization
    }
    response = requests.request(
        "get", f"http://localhost:8080/{user_id}/realms/master/users/profile",
        headers=headers
    )
    # print(response.content)
    return response.json()

