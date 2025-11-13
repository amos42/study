import pytest
from fastapi import APIRouter
from fastapi import Depends
from fastapi import FastAPI
from fastapi.testclient import TestClient


def get_user():
    return {"username": "test_user"}


my_router = APIRouter(prefix="/v1/access-controls")

@my_router.get("/")
def get_access_rules(user = Depends(get_user)):
    print(user)
    return {"a":user["username"]}


# =================================

router = APIRouter(prefix="/api/system-admin")
router.include_router(my_router)

# =================================

app = FastAPI()
app.include_router(router)

# =================================

client = TestClient(app)


def setUp():
    def mock_get_user():
        return {"username":"zzzz"}
    app.dependency_overrides[get_user] = mock_get_user

def tearDown():
    app.dependency_overrides.clear()


def test_get_access_controls(monkeypatch):
    setUp()

    response = client.get("/api/system-admin/v1/access-controls/")

    assert response.status_code == 200
    assert response.json() == {"a":"zzzz"}
    tearDown()


if __name__ == "__main__":
    pytest.main(["-s", "-v", __file__])

# if __name__ == "__main__":
#    uvicorn.run(
#        "main:app",
#        host="0.0.0.0",
#        port=8000,
#    )
