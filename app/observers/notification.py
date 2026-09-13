from app.observers.base import ReviewObserver
from app.repo import FavoriteRepository, NotificationRepository


class NotificationObserver(ReviewObserver):

    def __init__(
        self,
        favorite_repository: FavoriteRepository,
        notification_repository: NotificationRepository,
    ):
        self.favorite_repository = favorite_repository
        self.notification_repository = notification_repository

    async def update(
        self,
        user_id: int,
        media_id: int,
    ) -> None:

        user_ids = (
            await self.favorite_repository
            .get_users_who_favorited(media_id)
        )

        for favorite_user_id in user_ids:

            # Don't notify the person who submitted the review.
            if favorite_user_id == user_id:
                continue

            notification = await (
                self.notification_repository
                .create_notification(
                    user_id=favorite_user_id,
                    media_id=media_id,
                    message=(
                        f"New review added for media "
                        f"{media_id}."
                    ),
                )
            )