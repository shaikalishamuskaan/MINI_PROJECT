import asyncio
import csv
import logging
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.exc import IntegrityError

from app.db import AsyncSessionLocal
from app.repo import (
    FavoriteRepository,
    MediaRepository,
    NotificationRepository,
    ReviewRepository,
    UserRepository,
)
from app.services import ReviewService
from app.cache import CacheService
from app.observers.notification import NotificationObserver


logger = logging.getLogger(__name__)


def process_single_review(
    row: dict,
    user_id: int,
):
    """
    Process one review inside its own worker thread.

    Each worker creates its own database session so that
    AsyncSession objects are never shared between threads.
    """

    async def save_review():
        async with AsyncSessionLocal() as session:

            review_repository = ReviewRepository(session)
            user_repository = UserRepository(session)
            media_repository = MediaRepository(session)

            favorite_repository = FavoriteRepository(session)
            notification_repository = NotificationRepository(session)

            cache_service = CacheService()

            notification_observer = NotificationObserver(
                favorite_repository,
                notification_repository,
            )

            review_service = ReviewService(
                review_repository,
                user_repository,
                media_repository,
                cache_service=cache_service,
                observers=[notification_observer],
            )

            try:
                review = await review_service.create_review(
                    user_id=user_id,
                    media_id=int(row["media_id"]),
                    rating=int(row["rating"]),
                    comment=row["comment"],
                )

                logger.info(
                    "Bulk review created: user_id=%s media_id=%s",
                    user_id,
                    row["media_id"],
                )

                return True, review

            finally:
                await cache_service.close()

    try:
        return asyncio.run(save_review())

    except (ValueError, TypeError) as error:
        logger.warning(
            "Bulk review validation failed: "
            "user_id=%s media_id=%s error=%s",
            user_id,
            row.get("media_id"),
            error,
        )

        return False, error

    except IntegrityError as error:
        logger.warning(
            "Bulk review database constraint failed: "
            "user_id=%s media_id=%s",
            user_id,
            row.get("media_id"),
        )

        return False, error

    except Exception as error:
        logger.exception(
            "Unexpected bulk review failure: "
            "user_id=%s media_id=%s",
            user_id,
            row.get("media_id"),
        )

        return False, error


async def process_bulk_reviews(
    file_name: str,
    user_id: int,
    review_service: ReviewService,
):
    """
    Process reviews from a CSV file concurrently.
    """

    with open(
        file_name,
        "r",
        encoding="utf-8",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        required_columns = {
            "media_id",
            "rating",
            "comment",
        }

        if not required_columns.issubset(
            reader.fieldnames or set()
        ):
            raise ValueError(
                "CSV must contain media_id, rating, and comment columns."
            )

        rows = list(reader)

    if not rows:
        return 0, 0

    # For a single row, use the ReviewService supplied
    # by the caller. This keeps the same database/session
    # and preserves Redis + Observer integration.
    if len(rows) == 1:
        try:
            await review_service.create_review(
                user_id=user_id,
                media_id=int(rows[0]["media_id"]),
                rating=int(rows[0]["rating"]),
                comment=rows[0]["comment"],
            )

            logger.info(
                "Bulk review created: user_id=%s media_id=%s",
                user_id,
                rows[0]["media_id"],
            )

            return 1, 0

        except (
            ValueError,
            TypeError,
            IntegrityError,
        ) as error:

            logger.warning(
                "Bulk review failed: "
                "user_id=%s media_id=%s error=%s",
                user_id,
                rows[0].get("media_id"),
                error,
            )

            return 0, 1

    loop = asyncio.get_running_loop()

    successful = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=4) as executor:

        tasks = [
            loop.run_in_executor(
                executor,
                process_single_review,
                row,
                user_id,
            )
            for row in rows
        ]

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

    for result in results:

        if isinstance(result, Exception):
            failed += 1
            continue

        success, _ = result

        if success:
            successful += 1
        else:
            failed += 1

    logger.info(
        "Bulk review completed: "
        "user_id=%s successful=%s failed=%s",
        user_id,
        successful,
        failed,
    )

    return successful, failed