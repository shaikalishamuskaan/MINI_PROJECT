import asyncio
import csv
import logging
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.exc import IntegrityError

from app.db import AsyncSessionLocal
from app.repo import (
    MediaRepository,
    ReviewRepository,
    UserRepository,
)
from app.services import ReviewService

logger = logging.getLogger(__name__)


def process_single_review(
    user_id: int,
    media_id: int,
    rating: int,
    comment: str,
):
    """Process one review in a separate worker thread."""

    async def run_review():
        async with AsyncSessionLocal() as session:

            review_repository = ReviewRepository(session)
            user_repository = UserRepository(session)
            media_repository = MediaRepository(session)

            review_service = ReviewService(
                review_repository,
                user_repository,
                media_repository,
            )

            await review_service.create_review(
                user_id=user_id,
                media_id=media_id,
                rating=rating,
                comment=comment,
            )

    asyncio.run(run_review())


async def process_bulk_reviews(
    file_name: str,
    user_id: int,
    review_service: ReviewService,
):
    successful = 0
    failed = 0

    reviews = []

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

        for row in reader:
            try:
                reviews.append(
                    {
                        "media_id": int(row["media_id"]),
                        "rating": int(row["rating"]),
                        "comment": row["comment"],
                    }
                )

            except (ValueError, TypeError) as error:
                failed += 1

                logger.warning(
                    "Bulk review validation failed: "
                    "user_id=%s media_id=%s error=%s",
                    user_id,
                    row.get("media_id"),
                    error,
                )

    # Use the existing service for a single review.
    # This keeps the existing test and normal service flow compatible.
    if len(reviews) == 1:
        review = reviews[0]

        try:
            await review_service.create_review(
                user_id=user_id,
                media_id=review["media_id"],
                rating=review["rating"],
                comment=review["comment"],
            )

            successful += 1

        except (ValueError, TypeError) as error:
            failed += 1

            logger.warning(
                "Bulk review validation failed: "
                "user_id=%s media_id=%s error=%s",
                user_id,
                review["media_id"],
                error,
            )

        except IntegrityError:
            await review_service.review_repository.session.rollback()
            failed += 1

            logger.warning(
                "Bulk review failed due to database constraint: "
                "user_id=%s media_id=%s",
                user_id,
                review["media_id"],
            )

        logger.info(
            "Bulk review completed: "
            "user_id=%s successful=%s failed=%s",
            user_id,
            successful,
            failed,
        )

        return successful, failed

    # Process multiple reviews concurrently.
    loop = asyncio.get_running_loop()

    with ThreadPoolExecutor(max_workers=4) as executor:

        tasks = [
            loop.run_in_executor(
                executor,
                process_single_review,
                user_id,
                review["media_id"],
                review["rating"],
                review["comment"],
            )
            for review in reviews
        ]

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

    for result in results:

        if isinstance(result, Exception):
            failed += 1

            logger.warning(
                "Bulk review failed: %s",
                result,
            )

        else:
            successful += 1

    logger.info(
        "Bulk review completed: "
        "user_id=%s successful=%s failed=%s",
        user_id,
        successful,
        failed,
    )

    return successful, failed