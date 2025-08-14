from fastapi import FastAPI
from users.users import router as users_router
from apps.apps import router as apps_router
from posts.posts import router as posts_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# cors 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the API"}

# Include the routers
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(apps_router, prefix="/apps", tags=["apps"])
app.include_router(posts_router, prefix="/posts", tags=["posts"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0", port=8000)