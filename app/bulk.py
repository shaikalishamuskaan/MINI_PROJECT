import csv
import logging
logger = logging.getLogger(__name__)
from sqlalchemy.exc import IntegrityError
from app.services import ReviewService


async def process_bulk_reviews(
    file_name: str,
    user_id: int,
    review_service: ReviewService,
):
    successful = 0
    failed = 0

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

        if not required_columns.issubset(reader.fieldnames or set()):
            raise ValueError(
                "CSV must contain media_id, rating, and comment columns."
            )

        for row in reader:

            try:
                await review_service.create_review(
                    user_id=user_id,
                    media_id=int(row["media_id"]),
                    rating=int(row["rating"]),
                    comment=row["comment"],
                )

                successful += 1

                logger.info(
                    "Bulk review created: user_id=%s media_id=%s",
                    user_id,
                    row["media_id"],
                )

            except (ValueError, TypeError) as error:
                failed += 1
                logger.warning(
                    "Bulk review validation failed: user_id=%s media_id=%s error=%s",
                    user_id,
                    row.get("media_id"),
                    error,
                )
            
            except IntegrityError:
                await review_service.review_repository.session.rollback()
                failed += 1

                logger.warning(
                    "Bulk review failed due to database constraint: "
                    "user_id=%s media_id=%s",
                    user_id,
                    row.get("media_id"),
                )

    logger.info(
        "Bulk review completed: user_id=%s successful=%s failed=%s",
        user_id,
        successful,
        failed,
    )
    return successful, failed