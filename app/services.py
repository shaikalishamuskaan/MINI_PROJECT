import logging
import bcrypt
from app.repo import MediaRepository, ReviewRepository, UserRepository, FavoriteRepository
from app.media.factory import MediaFactory
logger = logging.getLogger(__name__)

class UserService:

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def create_user(self,username: str,password: str,):
        if not username.strip():
            raise ValueError("Username cannot be empty")

        if not password.strip():
            raise ValueError("Password cannot be empty")

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")

        return await self.user_repository.create_user(
            username=username,
            password_hash=password_hash,
        )

    async def get_user(self, user_id: int):
        user = await self.user_repository.get_user(user_id)

        if user is None:
            raise ValueError("User not found.")

        return user


class MediaService:

    def __init__(self, media_repository: MediaRepository):
        self.media_repository = media_repository

    async def create_media(
        self,
        title: str,
        media_type: str,
        genre: str,
        release_year: int,
    ):
        if not title.strip():
            raise ValueError("Title cannot be empty.")

        allowed_types = {"movie", "web_show", "song"}

        if media_type not in allowed_types:
            raise ValueError(
                "Media type must be movie, web_show, or song."
            )

        if not genre.strip():
            raise ValueError("Genre cannot be empty.")

        if release_year <= 0:
            raise ValueError("Release year must be positive.")

        media = MediaFactory.create_media(
            media_type=media_type,
            title=title,
            genre=genre,
            release_year=release_year,
        )

        return await self.media_repository.create_media(
            title=media.title,
            media_type=media.media_type,
            genre=media.genre,
            release_year=media.release_year,
        )

    async def get_media(self, media_id: int):
        media = await self.media_repository.get_media(media_id)

        if media is None:
            raise ValueError("Media not found.")

        return media

    async def search_media(self, title: str):
        if not title.strip():
            raise ValueError("Search title cannot be empty.")

        return await self.media_repository.search_media(title)
    async def get_all_media(self):
        return await self.media_repository.get_all_media()

class ReviewService:

    def __init__(
        self,
        review_repository: ReviewRepository,
        user_repository: UserRepository,
        media_repository: MediaRepository,
    ):
        self.review_repository = review_repository
        self.user_repository = user_repository
        self.media_repository = media_repository

    async def create_review(
        self,
        user_id: int,
        media_id: int,
        rating: int,
        comment: str,
    ):
        # Business validation
        if rating < 1 or rating > 5:
            logger.warning(
            "Invalid rating: user_id=%s media_id=%s rating=%s",
            user_id,
            media_id,
            rating,
        )
            raise ValueError("Rating must be between 1 and 5.")

        if not comment.strip():
            raise ValueError("Comment cannot be empty.")

        # Verify user exists
        user = await self.user_repository.get_user(user_id)

        if user is None:
            raise ValueError("User not found.")

        # Verify media exists
        media = await self.media_repository.get_media(media_id)

        if media is None:
            raise ValueError("Media not found.")
       # Save review
        review = await self.review_repository.create_review(
            user_id=user_id,
            media_id=media_id,
            rating=rating,
            comment=comment,
        )

        logger.info(
            "Review created: user_id=%s media_id=%s rating=%s",
            user_id,
            media_id,
            rating,
        )

        return review

    async def get_reviews(self, media_id: int):
        media = await self.media_repository.get_media(media_id)

        if media is None:
            raise ValueError("Media not found.")

        return await self.review_repository.get_reviews(media_id)

    async def get_top_rated(self, limit: int = 10):
        if limit <= 0:
            raise ValueError("Limit must be positive.")

        return await self.review_repository.get_top_rated(limit)
    
class FavoriteService:

    def __init__(
        self,
        favorite_repository: FavoriteRepository,
        user_repository: UserRepository,
        media_repository: MediaRepository,
    ):
        self.favorite_repository = favorite_repository
        self.user_repository = user_repository
        self.media_repository = media_repository

    async def add_favorite(
        self,
        user_id: int,
        media_id: int,
    ):
        user = await self.user_repository.get_user(user_id)

        if user is None:
            raise ValueError("User not found.")

        media = await self.media_repository.get_media(media_id)

        if media is None:
            raise ValueError("Media not found.")

        return await self.favorite_repository.add_favorite(
            user_id=user_id,
            media_id=media_id,
        )

    async def get_favorites(self, user_id: int):

        user = await self.user_repository.get_user(user_id)

        if user is None:
            raise ValueError("User not found.")

        return await self.favorite_repository.get_favorites(
            user_id
        )