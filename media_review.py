import argparse
import asyncio
import logging

from app.logging_config import setup_logging
from app.db import AsyncSessionLocal, create_tables
from app.repo import MediaRepository, UserRepository, ReviewRepository, FavoriteRepository, NotificationRepository
from app.services import MediaService, UserService, ReviewService, FavoriteService
from app.bulk import process_bulk_reviews
from app.recommendation import RecommendationEngine
from app.cache import CacheService
from app.observers.notification import NotificationObserver

def create_parser():
    parser = argparse.ArgumentParser(
        description="Media Review System"
    )

    parser.add_argument(
    "--add-user",
    nargs=2,
    metavar=("USERNAME", "PASSWORD"),
    help="Create a new user",
)

    parser.add_argument(
    "--add-media",
    nargs=4,
    metavar=("TITLE", "TYPE", "GENRE", "YEAR"),
    help="Add new media",
)
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all media",
    )

    parser.add_argument(
        "--search",
        type=str,
        help="Search media by title",
    )

    parser.add_argument(
        "--top-rated",
        action="store_true",
        help="Show top-rated media",
    )
    parser.add_argument(
    "--review",
    nargs=3,
    metavar=("MEDIA_ID", "RATING", "COMMENT"),
    help="Submit a review for media",
)

    parser.add_argument(    
        "--user-id",
        type=int,
        help="User submitting the review",
    )
    parser.add_argument(
        "--reviews",
        type=int,
        metavar="MEDIA_ID",
        help="Show reviews for media",
)
    parser.add_argument(
    "--favorite",
    type=int,
    metavar="MEDIA_ID",
    help="Add media to user's favorites",
)

    parser.add_argument(
    "--favorites",
    action="store_true",
    help="Show user's favorite media",
)
    parser.add_argument(
    "--bulk-review",
    type=str,
    metavar="FILE",
    help="Import reviews from a CSV file",
)

    parser.add_argument(
    "--recommend",
    type=int,
    metavar="USER_ID",
    help="Get personalized recommendations",
)

    return parser


async def main():

    setup_logging()

    logger = logging.getLogger(__name__)

    logger.info("Media Review System started")


    await create_tables()

    parser = create_parser()
    args = parser.parse_args()

    async with AsyncSessionLocal() as session:

        favorite_repository = FavoriteRepository(session)
        review_repository = ReviewRepository(session)
        user_repository = UserRepository(session)
        media_repository = MediaRepository(session)
        notification_repository=NotificationRepository(session)

        notification_observer = NotificationObserver(
            favorite_repository,
            notification_repository,
        )

        user_service = UserService(user_repository)
        media_service = MediaService(media_repository)

        cache_service = CacheService()

        review_service = ReviewService(
        review_repository,
        user_repository,
        media_repository,
        cache_service=cache_service,
        observers=[notification_observer],
    )
        favorite_service = FavoriteService(
        favorite_repository,
        user_repository,
        media_repository,
    )
        recommendation_engine = RecommendationEngine(
        review_repository,
        media_repository,
    )

        if args.add_user:
            username, password = args.add_user

            try:
                user = await user_service.create_user(
                    username=username,
                    password=password,
                )

                print(
                    f"User created successfully. "
                    f"ID: {user.id}, Username: {user.username}"
                )

            except ValueError as error:
                print(f"Error: {error}")
        
        elif args.add_media:

            title, media_type, genre, year = args.add_media

            try:
                media = await media_service.create_media(
                    title=title,
                    media_type=media_type,
                    genre=genre,
                    release_year=int(year),
                )

                print(
                    f"Media added successfully. "
                    f"ID: {media.id}, Title: {media.title}"
                )

            except ValueError as error:
                print(f"Error: {error}")

        elif args.list:

            media_list = await media_service.get_all_media()

            if not media_list:
                print("No media found.")
                return

            for media in media_list:
                print(
                    f"{media.id}. "
                    f"{media.title} | "
                    f"{media.media_type} | "
                    f"{media.genre} | "
                    f"{media.release_year}"
                )
        elif args.reviews:

            try:
                reviews = await review_service.get_reviews(
                    args.reviews
                )

                if not reviews:
                    print("No reviews found.")
                    return

                for review in reviews:
                    print(
                        f"Rating: {review.rating}/5 | "
                        f"Comment: {review.comment} | "
                        f"User ID: {review.user_id}"
                    )

            except ValueError as error:
                print(f"Error: {error}")


        elif args.review:

            if args.user_id is None:
                print("Error: --user-id is required to submit a review.")
                return

            media_id, rating, comment = args.review

            try:
                review = await review_service.create_review(
                    user_id=args.user_id,
                    media_id=int(media_id),
                    rating=int(rating),
                    comment=comment,
                )

                print(
                    f"Review submitted successfully. "
                    f"Review ID: {review.id}"
                )

            except ValueError as error:
                print(f"Error: {error}")

        elif args.search:

            try:
                media_list = await media_service.search_media(
                    args.search
                )

                if not media_list:
                    print("No media found.")
                    return

                for media in media_list:
                    print(
                        f"{media.id}. "
                        f"{media.title} | "
                        f"{media.media_type} | "
                        f"{media.genre} | "
                        f"{media.release_year}"
                    )

            except ValueError as error:
                print(f"Error: {error}")

        elif args.top_rated:

            try:
                top_media = await review_service.get_top_rated()

                if not top_media:
                    print("No rated media found.")
                    return

                for media, average_rating in top_media:
                    print(
                        f"{media.id}. "
                        f"{media.title} | "
                        f"{media.media_type} | "
                        f"Average Rating: "
                        f"{average_rating:.2f}/5"
                    )

            except ValueError as error:
                print(f"Error: {error}")

        elif args.favorite:

            if args.user_id is None:
                print("Error: --user-id is required.")
                return

            try:
                favorite = await favorite_service.add_favorite(
                    user_id=args.user_id,
                    media_id=args.favorite,
                )

                print(
                    f"Media {favorite.media_id} "
                    f"added to favorites."
                )

            except ValueError as error:
                print(f"Error: {error}")
        elif args.favorites:

            if args.user_id is None:
                print("Error: --user-id is required.")
                return

            try:
                favorites = await favorite_service.get_favorites(
                    args.user_id
                )

                if not favorites:
                    print("No favorites found.")
                    return

                for media in favorites:
                    print(
                        f"{media.id}. "
                        f"{media.title} | "
                        f"{media.media_type} | "
                        f"{media.genre} | "
                        f"{media.release_year}"
                    )

            except ValueError as error:
                print(f"Error: {error}")
        elif args.bulk_review:

            if args.user_id is None:
                print("Error: --user-id is required.")
                return

            try:
                successful, failed = await process_bulk_reviews(
                    file_name=args.bulk_review,
                    user_id=args.user_id,
                    review_service=review_service,
                )

                print(
                    f"Bulk review completed. "
                    f"Successful: {successful}, "
                    f"Failed: {failed}"
                )

            except FileNotFoundError:
                print("Error: Review file not found.")

            except ValueError as error:
                print(f"Error: {error}")

        elif args.recommend:

                try:
                    recommendations = (
                        await recommendation_engine.recommend(
                            user_id=args.recommend,
                        )
                    )

                    if not recommendations:
                        print("No recommendations available.")
                        return

                    print("Recommended for you:")

                    for item in recommendations:
                        print(
                            f"{item['media_id']}. "
                            f"{item['title']} | "
                            f"{item['genre']} | "
                            f"Rating: {item['average_rating']:.2f} | "
                            f"Score: {item['score']:.2f}"
                        )

                except ValueError as error:
                    print(f"Error: {error}")

        else:
            parser.print_help()

        await cache_service.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication stopped.")
    except Exception as error:
        logger = logging.getLogger(__name__)
        logger.exception("Unexpected application error")
        print(f"Error: {error}")