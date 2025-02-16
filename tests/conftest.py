from httpx import ASGITransport, AsyncClient
from faker import Faker
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.config import get_settings
from app.database import get_async_session
from app.main import app
from app.models import Link

# Create an async in-memory SQLite database
engine = create_async_engine(get_settings().test_database_url, echo=True, future=True)
get_async_session_override = async_sessionmaker(bind=engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def async_session():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    async with get_async_session_override() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def async_client(async_session: AsyncSession):
    async def get_session_override():
        yield async_session

    app.dependency_overrides[get_async_session] = get_session_override

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function", name="faker")
async def fresh_faker() -> Faker:
    return Faker()


@pytest_asyncio.fixture(scope="function")
async def fake_link(async_session: AsyncSession, faker: Faker) -> Link:
    link = Link(
        full_url=faker.url(),
        shortcut=faker.bothify("?" * 6),
        visits=faker.random_int(0, 100),
        creator_ip=faker.ipv4(),
        creator_user_agent=faker.user_agent(),
    )
    async_session.add(link)
    await async_session.commit()
    await async_session.refresh(link)
    return link


@pytest.fixture
def random_shortcut(faker: Faker) -> str:
    return faker.bothify("?" * 6)
