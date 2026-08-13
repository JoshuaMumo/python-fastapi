from fastapi import FastAPI, HTTPException
from app.schemas import PostCreate, PostResponse
from app.db import Post, create_db_and_tables, get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/hello-world")
def hello_world():
    return {"message":"Hello World"} 

text_posts = {
    1: {"title": "New Post", "content": "cool test post"},
    2: {"title": "Getting Started", "content": "This is my first post on the platform."},
    3: {"title": "Python Programming", "content": "Python is a powerful and beginner-friendly programming language."},
    4: {"title": "Weekend Plans", "content": "Looking forward to having a great weekend."},
    5: {"title": "Technology News", "content": "Technology continues to change the way we work and communicate."},
    6: {"title": "Learning React", "content": "Today I started learning React and building simple components."},
    7: {"title": "Coding Practice", "content": "The best way to improve programming skills is to practice consistently."},
    8: {"title": "Project Update", "content": "I have made good progress on my latest software project."},
    9: {"title": "Useful Tip", "content": "Always break a large programming problem into smaller, manageable tasks."},
    10: {"title": "Good Morning", "content": "Wishing everyone a productive and successful day."}
}
@app.get("/posts")
def get_all_posts(limit: int = None):
    if limit:
        return list(text_posts.values())[:limit]
    return text_posts


@app.get(f"/posts/{id}")
def get_post(id: int)-> PostResponse:
    if id not in text_posts:
        raise HTTPException(status_code=404, detail="Post not found")
    return text_posts.get(id) 

@app.post("/posts")
def create_post(post: PostCreate) -> PostResponse:
    new_post = {"title":post.title, "content":post.content}
    text_posts[max(text_posts.keys()) + 1] = new_post
    return new_post

