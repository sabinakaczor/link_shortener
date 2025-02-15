from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.config import get_settings

engine = create_async_engine(get_settings().database_url, echo=True, future=True)
async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
