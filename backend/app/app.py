from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from app.db import Post, create_db_and_tables, get_async_session, User
from app.images import imagekit
from app.schemas import UserRead, UserCreate, UserUpdate
from app.users import auth_backend, current_active_user, fastapi_users
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select
import uuid



@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"])
app.include_router(fastapi_users.get_register_router(UserRead, UserCreate), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_verify_router(UserRead), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix="/users", tags=["users"])


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    user:User = Depends(current_active_user),
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
            user_id=user.id,
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
    session: AsyncSession = Depends(get_async_session),
     user:User = Depends(current_active_user),
):
    result = await session.execute(
        select(Post).order_by(Post.created_at.desc())
    )

    posts = result.scalars().all()

    result = await session.execute(select(User))
    users = [row[0] for row in result.all()]
    user_dict = {u.id: u.email for u in users}

    posts_data = []

    for post in posts:
        posts_data.append({
            "id": str(post.id),
            "user_id":str(post.user_id),
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at": post.created_at.isoformat(),
            "is_owner":post.user_id==user.id,
            "email":user_dict.get(post.user_id, "unknown")
        })

    return {"posts": posts_data}

@app.delete("/posts/{post_id}")
async def delete_post(
    post_id: str,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    try:
        post_uuid = uuid.UUID(post_id)

        result = await session.execute(
            select(Post).where(Post.id == post_uuid)
        )

        post = result.scalars().first()

        if not post:
            raise HTTPException(
                status_code=404,
                detail="Post not found"
            )

        if post.user_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to delete this post"
            )

        await session.delete(post)
        await session.commit()

        return {
            "success": True,
            "message": "Post deleted successfully"
        }

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid post ID"
        )

    except HTTPException:
        raise

    except Exception as e:
        await session.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )