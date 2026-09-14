import pytest

from app.auth import AuthService
from app.repo import UserRepository
from app.services import UserService

import pytest_asyncio

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)




from app.models import Base


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
async def test_login_success(session):

    repository = UserRepository(session)

    user_service = UserService(repository)

    await user_service.create_user(
        username="alisha",
        password="test_password",
    )

    auth_service = AuthService(repository)

    user = await auth_service.login(
        username="alisha",
        password="test_password",
    )

    assert user is not None
    assert user.username == "alisha"


@pytest.mark.asyncio
async def test_login_wrong_password(session):

    repository = UserRepository(session)

    user_service = UserService(repository)

    await user_service.create_user(
        username="alisha",
        password="test_password",
    )

    auth_service = AuthService(repository)

    with pytest.raises(
        ValueError,
        match="Invalid username or password",
    ):
        await auth_service.login(
            username="alisha",
            password="wrong_password",
        )


@pytest.mark.asyncio
async def test_login_unknown_user(session):

    repository = UserRepository(session)

    auth_service = AuthService(repository)

    with pytest.raises(
        ValueError,
        match="Invalid username or password",
    ):
        await auth_service.login(
            username="does_not_exist",
            password="test_password",
        )


@pytest.mark.asyncio
async def test_login_empty_username(session):

    repository = UserRepository(session)

    auth_service = AuthService(repository)

    with pytest.raises(
        ValueError,
        match="Username cannot be empty",
    ):
        await auth_service.login(
            username="",
            password="test_password",
        )


@pytest.mark.asyncio
async def test_login_empty_password(session):

    repository = UserRepository(session)

    auth_service = AuthService(repository)

    with pytest.raises(
        ValueError,
        match="Password cannot be empty",
    ):
        await auth_service.login(
            username="alisha",
            password="",
        )