from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def read_posts():
    return {"message": "게시글 목록 가져오기"}

@router.post("/")
def create_post(title: str, content: str):
    return {"message": "게시글 생성", "title": title, "content": content}

@router.get("/{post_id}")
def read_post(post_id: int):
    return {"message": f"게시글 {post_id} 가져오기"}
