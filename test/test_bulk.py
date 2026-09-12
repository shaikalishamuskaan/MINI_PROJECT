import pytest
import pytest_asyncio

from app.bulk import process_bulk_reviews
from app.models import Base
from app.repo import (
    MediaRepository,
    ReviewRepository,
    UserRepository,
)
from app.services import (
    ReviewService,
    UserService,
    MediaService,
)

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
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
async def test_bulk_review_import(session, tmp_path):

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

    csv_file = tmp_path / "reviews.csv"

    csv_file.write_text(
        "media_id,rating,comment\n"
        f"{media.id},5,Amazing movie\n"
    )

    successful, failed = await process_bulk_reviews(
        file_name=str(csv_file),
        user_id=user.id,
        review_service=review_service,
    )

    assert successful == 1
    assert failed == 0

    reviews = await review_service.get_reviews(media.id)

    assert len(reviews) == 1
    assert reviews[0].rating == 5