from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Favorite, Media, Review, User


class UserRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(
        self,
        username: str,
        password_hash: str,
    ) -> User:

        user = User(
            username=username,
            password_hash=password_hash,
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        return user

    async def get_user(self, user_id: int) -> User | None:

        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )

        return result.scalar_one_or_none()
class MediaRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_media(
        self,
        title: str,
        media_type: str,
        genre: str,
        release_year: int,
    ) -> Media:

        media = Media(
            title=title,
            media_type=media_type,
            genre=genre,
            release_year=release_year,
        )

        self.session.add(media)
        await self.session.commit()
        await self.session.refresh(media)

        return media

    async def get_media(self, media_id: int) -> Media | None:

        result = await self.session.execute(
            select(Media).where(Media.id == media_id)
        )

        return result.scalar_one_or_none()

    async def get_all_media(self) -> list[Media]:

        result = await self.session.execute(
            select(Media).order_by(Media.id)
        )

        return list(result.scalars().all())

    async def search_media(self, title: str) -> list[Media]:

        result = await self.session.execute(
            select(Media)
            .where(Media.title.ilike(f"%{title}%"))
            .order_by(Media.title)
        )

        return list(result.scalars().all())

class ReviewRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_review(
        self,
        user_id: int,
        media_id: int,
        rating: int,
        comment: str,
    ) -> Review:

        review = Review(
            user_id=user_id,
            media_id=media_id,
            rating=rating,
            comment=comment,
        )

        self.session.add(review)
        await self.session.commit()
        await self.session.refresh(review)

        return review

    async def get_reviews(
        self,
        media_id: int,
    ) -> list[Review]:

        result = await self.session.execute(
            select(Review)
            .where(Review.media_id == media_id)
            .order_by(Review.created_at.desc())
        )

        return list(result.scalars().all())

    async def get_top_rated(
        self,
        limit: int = 10,
    ) -> list[tuple[Media, float]]:

        result = await self.session.execute(
            select(
                Media,
                func.avg(Review.rating).label("average_rating"),
            )
            .join(Review, Media.id == Review.media_id)
            .group_by(Media.id)
            .order_by(func.avg(Review.rating).desc())
            .limit(limit)
        )

        return list(result.all())

class FavoriteRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_favorite(
        self,
        user_id: int,
        media_id: int,
    ) -> Favorite:

        favorite = Favorite(
            user_id=user_id,
            media_id=media_id,
        )

        self.session.add(favorite)
        await self.session.commit()

        return favorite

    async def get_favorites(
        self,
        user_id: int,
    ) -> list[Media]:

        result = await self.session.execute(
            select(Media)
            .join(Favorite, Media.id == Favorite.media_id)
            .where(Favorite.user_id == user_id)
        )

        return list(result.scalars().all())

async def get_all_media(self) -> list[Media]:

    result = await self.session.execute(
        select(Media).order_by(Media.id)
    )

    return list(result.scalars().all())