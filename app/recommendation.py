from app.repo import MediaRepository, ReviewRepository


class RecommendationEngine:

    def __init__(
        self,
        review_repository: ReviewRepository,
        media_repository: MediaRepository,
    ):
        self.review_repository = review_repository
        self.media_repository = media_repository

    async def recommend(
        self,
        user_id: int,
        limit: int = 5,
    ):
        # Get media already reviewed by this user
        reviewed_media_ids = (
            await self.review_repository
            .get_user_reviewed_media_ids(user_id)
        )

        # Get statistics for media that already have reviews
        statistics = (
            await self.review_repository
            .get_rating_statistics()
        )

        # Get all media so that even unrated media
        # can be considered for recommendations
        all_media = (
            await self.media_repository
            .get_all_media()
        )

        if not all_media:
            return []

        # Get user's genre preferences
        genre_ratings = (
            await self.review_repository
            .get_user_genre_ratings(user_id)
        )

        genre_preferences = {
            genre: float(average_rating)
            for genre, average_rating in genre_ratings
        }

        # Get user's media type preferences
        media_type_ratings = (
            await self.review_repository
            .get_user_media_type_ratings(user_id)
        )

        media_type_preferences = {
            media_type: float(average_rating)
            for media_type, average_rating in media_type_ratings
        }

        # Get global rating statistics
        global_stats = (
            await self.review_repository
            .get_global_rating_statistics()
        )

        total_rating = int(
            global_stats.total_rating or 0
        )

        total_rating_count = int(
            global_stats.rating_count or 0
        )

        if total_rating_count == 0:
            return []

        overall_average = (
            total_rating / total_rating_count
        )

        minimum_votes = 2

        # Convert rated media statistics into a dictionary
        rated_media = {
            row.id: row
            for row in statistics
        }

        recommendations = []

        for media in all_media:

            # Never recommend media already reviewed
            # by the current user
            if media.id in reviewed_media_ids:
                continue

            row = rated_media.get(media.id)

            # ------------------------------------------
            # MEDIA HAS REVIEWS
            # ------------------------------------------

            if row:

                average_rating = float(
                    row.average_rating
                )

                media_rating_count = int(
                    row.rating_count
                )

                # Bayesian / weighted rating
                weighted_rating = (
                    (
                        media_rating_count
                        / (
                            media_rating_count
                            + minimum_votes
                        )
                    )
                    * average_rating
                    +
                    (
                        minimum_votes
                        / (
                            media_rating_count
                            + minimum_votes
                        )
                    )
                    * overall_average
                )

            # ------------------------------------------
            # MEDIA HAS NO REVIEWS
            # ------------------------------------------

            else:

                average_rating = 0.0
                media_rating_count = 0

                # Use the global average as the
                # baseline for unrated media
                weighted_rating = overall_average

            # ------------------------------------------
            # GENRE PREFERENCE
            # ------------------------------------------

            genre_preference = genre_preferences.get(
                media.genre,
                overall_average,
            )

            genre_bonus = (
                genre_preference
                - overall_average
            ) * 0.2

            # ------------------------------------------
            # MEDIA TYPE PREFERENCE
            # ------------------------------------------

            media_type_preference = (
                media_type_preferences.get(
                    media.media_type,
                    overall_average,
                )
            )

            media_type_bonus = (
                media_type_preference
                - overall_average
            ) * 0.1

            # ------------------------------------------
            # FINAL SCORE
            # ------------------------------------------

            final_score = (
                weighted_rating
                + genre_bonus
                + media_type_bonus
            )

            recommendations.append(
                {
                    "media_id": media.id,
                    "title": media.title,
                    "genre": media.genre,
                    "average_rating": average_rating,
                    "rating_count": media_rating_count,
                    "score": final_score,
                }
            )

        # Highest recommendation score first
        recommendations.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return recommendations[:limit]