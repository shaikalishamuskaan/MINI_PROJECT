import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models import Base
from app.repo import MediaRepository, UserRepository


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:"
    )

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with SessionLocal() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_create_user(session):
    repository = UserRepository(session)

    user = await repository.create_user(
        username="alisha",
        password_hash="hashed_password",
    )

    assert user.id is not None
    assert user.username == "alisha"


@pytest.mark.asyncio
async def test_create_media(session):
    repository = MediaRepository(session)

    media = await repository.create_media(
        title="Inception",
        media_type="movie",
        genre="Sci-Fi",
        release_year=2010,
    )

    assert media.id is not None
    assert media.title == "Inception"