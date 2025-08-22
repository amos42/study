from typing import Any
from uuid import UUID
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from ..auth.auth import User, get_user_from_token
import requests

router = APIRouter()

@router.get("/")
def read_users(user_info: User = Depends(get_user_from_token)) -> list[User]:
    return [user_info]

@router.post("/")
def create_user(name: str, email: str, user_info: User = Depends(get_user_from_token)):
    return {"message": "사용자 생성", "name": name, "email": email, "created_by": user_info.username}

@router.get("/{user_id}")
def read_user(user_id: str, user_info: User = Depends(get_user_from_token), authorization: str = Header(None)) -> Any:
    headers = {
        "Content-Type": "application/json",
        "Authorization": authorization
    }
    response = requests.request(
        "get", f"http://localhost:8080/admin/realms/master/users/{user_id}",
        headers=headers
    )
    
    return response.json()

@router.put("/{user_id}")
def update_user(user_id: str, user_info: User = Depends(get_user_from_token), authorization: str = Header(None)) -> Any:
    headers = {
        "Content-Type": "application/json",
        "Authorization": authorization
    }
    response = requests.request(
        "put", f"http://localhost:8080/admin/realms/master/users/{user_id}",
        headers=headers,
        json={
            "attributes": {
                "company": "S-Core",
                "department": "Employee"
            }
        }
    )
    
    return response.json()

