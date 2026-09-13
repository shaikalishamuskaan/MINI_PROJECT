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
    FavoriteRepository,
)
from app.services import (
    MediaService,
    ReviewService,
    UserService,
    FavoriteService,
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
        password="test_password",
    )

    assert user.username == "alisha"


@pytest.mark.asyncio
async def test_user_service_rejects_empty_username(session):

    repository = UserRepository(session)
    service = UserService(repository)

    with pytest.raises(ValueError, match="Username cannot be empty"):
        await service.create_user(
            username="",
            password="test_password",
        )


@pytest.mark.asyncio
async def test_user_service_rejects_empty_password(session):

    repository = UserRepository(session)
    service = UserService(repository)

    with pytest.raises(ValueError, match="Password cannot be empty"):
        await service.create_user(
            username="alisha",
            password="",
        )
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
async def test_media_service_rejects_empty_title(session):

    repository = MediaRepository(session)
    service = MediaService(repository)

    with pytest.raises(ValueError, match="Title cannot be empty"):
        await service.create_media(
            title="",
            media_type="movie",
            genre="Sci-Fi",
            release_year=2010,
        )


@pytest.mark.asyncio
async def test_media_service_rejects_invalid_media_type(session):

    repository = MediaRepository(session)
    service = MediaService(repository)

    with pytest.raises(
        ValueError,
        match="Media type must be movie, web_show, or song",
    ):
        await service.create_media(
            title="Inception",
            media_type="book",
            genre="Sci-Fi",
            release_year=2010,
        )

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
async def test_review_service_rejects_empty_comment(session):

    user_repository = UserRepository(session)
    media_repository = MediaRepository(session)
    review_repository = ReviewRepository(session)

    service = ReviewService(
        review_repository,
        user_repository,
        media_repository,
    )

    with pytest.raises(ValueError, match="Comment cannot be empty"):
        await service.create_review(
            user_id=1,
            media_id=1,
            rating=5,
            comment="",
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
        password="test_password",
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
        password="test_password",
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
async def test_review_service_rejects_nonexistent_user(session):

    user_repository = UserRepository(session)
    media_repository = MediaRepository(session)
    review_repository = ReviewRepository(session)

    service = ReviewService(
        review_repository,
        user_repository,
        media_repository,
    )

    with pytest.raises(ValueError, match="User not found"):
        await service.create_review(
            user_id=999,
            media_id=1,
            rating=5,
            comment="Great movie",
        )


@pytest.mark.asyncio
async def test_review_service_rejects_nonexistent_media(session):

    user_repository = UserRepository(session)
    media_repository = MediaRepository(session)
    review_repository = ReviewRepository(session)

    user_service = UserService(user_repository)

    user = await user_service.create_user(
        username="alisha",
        password="test_password",
    )

    service = ReviewService(
        review_repository,
        user_repository,
        media_repository,
    )

    with pytest.raises(ValueError, match="Media not found"):
        await service.create_review(
            user_id=user.id,
            media_id=999,
            rating=5,
            comment="Great movie",
        )

@pytest.mark.asyncio
async def test_review_service_get_top_rated(session):

    user_repository = UserRepository(session)
    media_repository = MediaRepository(session)
    review_repository = ReviewRepository(session)

    user_service = UserService(user_repository)
    media_service = MediaService(media_repository)

    user = await user_service.create_user(
        username="alisha",
        password="test_password",
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

@pytest.mark.asyncio
async def test_favorite_service_adds_favorite(session):

    user_repository = UserRepository(session)
    media_repository = MediaRepository(session)
    favorite_repository = FavoriteRepository(session)

    user_service = UserService(user_repository)
    media_service = MediaService(media_repository)

    user = await user_service.create_user(
        username="alisha",
        password="test_password",
    )

    media = await media_service.create_media(
        title="Inception",
        media_type="movie",
        genre="Sci-Fi",
        release_year=2010,
    )

    favorite_service = FavoriteService(
        favorite_repository,
        user_repository,
        media_repository,
    )

    favorite = await favorite_service.add_favorite(
        user_id=user.id,
        media_id=media.id,
    )

    assert favorite.user_id == user.id
    assert favorite.media_id == media.id

@pytest.mark.asyncio
async def test_favorite_service_get_favorites(session):

    user_repository = UserRepository(session)
    media_repository = MediaRepository(session)
    favorite_repository = FavoriteRepository(session)

    user_service = UserService(user_repository)
    media_service = MediaService(media_repository)

    user = await user_service.create_user(
        username="alisha",
        password="test_password",
    )

    media = await media_service.create_media(
        title="Inception",
        media_type="movie",
        genre="Sci-Fi",
        release_year=2010,
    )

    favorite_service = FavoriteService(
        favorite_repository,
        user_repository,
        media_repository,
    )

    await favorite_service.add_favorite(
        user_id=user.id,
        media_id=media.id,
    )

    favorites = await favorite_service.get_favorites(
        user.id
    )

    assert len(favorites) == 1
    assert favorites[0].title == "Inception"