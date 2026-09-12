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
from app.recommendation import RecommendationEngine
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
async def test_recommendations_exclude_reviewed_media(session):

    user_repository = UserRepository(session)
    media_repository = MediaRepository(session)
    review_repository = ReviewRepository(session)

    user_service = UserService(user_repository)
    media_service = MediaService(media_repository)

    user = await user_service.create_user(
        username="alisha",
        password_hash="hashed_password",
    )

    reviewed_media = await media_service.create_media(
        title="Inception",
        media_type="movie",
        genre="Sci-Fi",
        release_year=2010,
    )

    recommended_media = await media_service.create_media(
        title="Interstellar",
        media_type="movie",
        genre="Sci-Fi",
        release_year=2014,
    )

    review_service = ReviewService(
        review_repository,
        user_repository,
        media_repository,
    )

    await review_service.create_review(
        user_id=user.id,
        media_id=reviewed_media.id,
        rating=5,
        comment="Amazing",
    )

    # Give the unreviewed media a rating so it becomes
    # a recommendation candidate.
    another_user = await user_service.create_user(
        username="testuser",
        password_hash="hashed_password",
    )

    await review_service.create_review(
        user_id=another_user.id,
        media_id=recommended_media.id,
        rating=5,
        comment="Great",
    )

    engine = RecommendationEngine(review_repository)

    recommendations = await engine.recommend(
        user_id=user.id
    )

    recommended_ids = {
        item["media_id"]
        for item in recommendations
    }

    assert reviewed_media.id not in recommended_ids
    assert recommended_media.id in recommended_ids

@pytest.mark.asyncio
async def test_recommendation_limit(session):

    user_repository = UserRepository(session)
    media_repository = MediaRepository(session)
    review_repository = ReviewRepository(session)

    user_service = UserService(user_repository)
    media_service = MediaService(media_repository)

    user = await user_service.create_user(
        username="alisha",
        password_hash="hashed_password",
    )

    for i in range(5):
        media = await media_service.create_media(
            title=f"Movie {i}",
            media_type="movie",
            genre="Sci-Fi",
            release_year=2020 + i,
        )

        other_user = await user_service.create_user(
            username=f"user{i}",
            password_hash="hashed_password",
        )

        review_service = ReviewService(
            review_repository,
            user_repository,
            media_repository,
        )

        await review_service.create_review(
            user_id=other_user.id,
            media_id=media.id,
            rating=5,
            comment="Great",
        )

    engine = RecommendationEngine(review_repository)

    recommendations = await engine.recommend(
        user_id=user.id,
        limit=3,
    )

    assert len(recommendations) == 3