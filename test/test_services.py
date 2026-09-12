import pytest
import pytest_asyncio

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models import Base
from app.repo import (
    MediaRepository,
    ReviewRepository,
    UserRepository,
)
from app.services import (
    MediaService,
    ReviewService,
    UserService,
)


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
async def test_user_service_creates_user(session):

    repository = UserRepository(session)
    service = UserService(repository)

    user = await service.create_user(
        username="alisha",
        password_hash="hashed_password",
    )

    assert user.username == "alisha"


@pytest.mark.asyncio
async def test_media_service_creates_media(session):

    repository = MediaRepository(session)
    service = MediaService(repository)

    media = await service.create_media(
        title="Inception",
        media_type="movie",
        genre="Sci-Fi",
        release_year=2010,
    )

    assert media.title == "Inception"


@pytest.mark.asyncio
async def test_review_service_rejects_invalid_rating(session):

    user_repository = UserRepository(session)
    media_repository = MediaRepository(session)
    review_repository = ReviewRepository(session)

    service = ReviewService(
        review_repository,
        user_repository,
        media_repository,
    )

    with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
        await service.create_review(
            user_id=1,
            media_id=1,
            rating=6,
            comment="Great movie",
        )

@pytest.mark.asyncio
async def test_review_service_creates_review(session):

    user_repository = UserRepository(session)
    media_repository = MediaRepository(session)
    review_repository = ReviewRepository(session)

    user_service = UserService(user_repository)
    media_service = MediaService(media_repository)

    user = await user_service.create_user(
        username="alisha",
        password_hash="hashed_password",
    )

    media = await media_service.create_media(
        title="Inception",
        media_type="movie",
        genre="Sci-Fi",
        release_year=2010,
    )

    review_service = ReviewService(
        review_repository,
        user_repository,
        media_repository,
    )

    review = await review_service.create_review(
        user_id=user.id,
        media_id=media.id,
        rating=5,
        comment="Amazing movie",
    )

    assert review.id is not None
    assert review.rating == 5
    assert review.comment == "Amazing movie"

@pytest.mark.asyncio
async def test_review_service_get_reviews(session):

    user_repository = UserRepository(session)
    media_repository = MediaRepository(session)
    review_repository = ReviewRepository(session)

    user_service = UserService(user_repository)
    media_service = MediaService(media_repository)

    user = await user_service.create_user(
        username="alisha",
        password_hash="hashed_password",
    )

    media = await media_service.create_media(
        title="Inception",
        media_type="movie",
        genre="Sci-Fi",
        release_year=2010,
    )

    review_service = ReviewService(
        review_repository,
        user_repository,
        media_repository,
    )

    await review_service.create_review(
        user_id=user.id,
        media_id=media.id,
        rating=5,
        comment="Amazing movie",
    )

    reviews = await review_service.get_reviews(
        media.id
    )

    assert len(reviews) == 1
    assert reviews[0].rating == 5
    
@pytest.mark.asyncio
async def test_review_service_get_top_rated(session):

    user_repository = UserRepository(session)
    media_repository = MediaRepository(session)
    review_repository = ReviewRepository(session)

    user_service = UserService(user_repository)
    media_service = MediaService(media_repository)

    user = await user_service.create_user(
        username="alisha",
        password_hash="hashed_password",
    )

    media = await media_service.create_media(
        title="Inception",
        media_type="movie",
        genre="Sci-Fi",
        release_year=2010,
    )

    review_service = ReviewService(
        review_repository,
        user_repository,
        media_repository,
    )

    await review_service.create_review(
        user_id=user.id,
        media_id=media.id,
        rating=5,
        comment="Amazing",
    )

    results = await review_service.get_top_rated()

    assert len(results) == 1

    result_media, average_rating = results[0]

    assert result_media.title == "Inception"
    assert average_rating == 5