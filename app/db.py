from collections.abc import AsyncGenerator
from types import AsyncGeneratorType
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship
import datetime
from datetime import datetime
from zoneinfo import ZoneInfo

DATABASE_URL="sqlite+aiosqlite:///./test.db"

class Base(DeclarativeBase):
    pass

class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    caption = Column(Text)
    url=Column(String, nullable=False)
    file_type=Column(String, nullable=False)
    file_name=Column(String, nullable=False)
    created_at=Column(DateTime, default=datetime.now(ZoneInfo("Africa/Nairobi")))

engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

# starts engine and creates database and tables
async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# access, read and write in database asynchronously
async def get_async_session()-> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session