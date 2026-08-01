import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from nucleus_api.core.config import settings
from nucleus_api.db.base import Base
from nucleus_api.models.refresh_token import RefreshToken  # noqa: F401 - registers with Base.metadata
from nucleus_api.models.user import User  # noqa: F401 - registers with Base.metadata

TEST_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_host}:{settings.postgres_port}/nucleus_test"
)


@pytest.fixture
async def db_session():
    """
    Fresh schema per test: create all tables before, drop all after.
    Each test is fully isolated — no shared state across tests.
    """
    engine = create_async_engine(TEST_DATABASE_URL)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
