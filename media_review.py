import argparse
import asyncio


from app.db import AsyncSessionLocal, create_tables
from app.repo import MediaRepository, UserRepository, ReviewRepository
from app.services import MediaService, UserService, ReviewService

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

    return parser


async def main():

    await create_tables()

    parser = create_parser()
    args = parser.parse_args()

    async with AsyncSessionLocal() as session:
         
        review_repository = ReviewRepository(session)
        user_repository = UserRepository(session)
        media_repository = MediaRepository(session)

        user_service = UserService(user_repository)
        media_service = MediaService(media_repository)
        review_service = ReviewService(
        review_repository,
        user_repository,
        media_repository,
    )

        if args.add_user:
            username, password = args.add_user

            try:
                user = await user_service.create_user(
                    username=username,
                    password_hash=password,
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
            print(f"Searching for: {args.search}")
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

        else:
            parser.print_help()
if __name__ == "__main__":
    asyncio.run(main())