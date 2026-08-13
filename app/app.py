from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from app.db import Post, create_db_and_tables, get_async_session
from app.images import imagekit
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(""),
    session: AsyncSession = Depends(get_async_session)
):
    try:
        # Read the uploaded file
        file_data = await file.read()

        # Upload to ImageKit
        upload_result = imagekit.files.upload(
            file=file_data,
            file_name=file.filename,
        )

        # Determine file type
        if file.content_type and file.content_type.startswith("video/"):
            file_type = "video"
        else:
            file_type = "image"

        # Save information in database
        post = Post(
            caption=caption,
            url=upload_result.url,
            file_type=file_type,
            file_name=upload_result.name,
        )

        session.add(post)
        await session.commit()
        await session.refresh(post)

        return post

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/feed")
async def get_feed(
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(Post).order_by(Post.created_at.desc())
    )

    posts = result.scalars().all()

    posts_data = []

    for post in posts:
        posts_data.append({
            "id": str(post.id),
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at": post.created_at.isoformat()
        })

    return {"posts": posts_data}