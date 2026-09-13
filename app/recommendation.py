from app.repo import ReviewRepository


class RecommendationEngine:
    def __init__(self, review_repository: ReviewRepository):
        self.review_repository = review_repository


    async def recommend(
        self,
        user_id: int,
        limit: int = 5,
    ):
        reviewed_media_ids = (
            await self.review_repository.get_user_reviewed_media_ids(
                user_id
            )
        )

        statistics = (
            await self.review_repository.get_rating_statistics()
        )

        if not statistics:
            return []

        genre_ratings = (
            await self.review_repository.get_user_genre_ratings(
                user_id
            )
        )

        media_type_ratings = (
            await self.review_repository.get_user_media_type_ratings(
                user_id
            )
        )

        genre_preferences = {
            genre: float(average_rating)
            for genre, average_rating in genre_ratings
        }

        media_type_preferences = {
            media_type: float(average_rating)
            for media_type, average_rating in media_type_ratings
        }

        global_stats = (
            await self.review_repository.get_global_rating_statistics()
        )

        total_rating = int(global_stats.total_rating or 0)
        rating_count = int(global_stats.rating_count or 0)

        if rating_count == 0:
            return []

        overall_average = total_rating / rating_count

        minimum_votes = 2

        recommendations = []

        for row in statistics:
            if row.id in reviewed_media_ids:
                continue

            average_rating = float(row.average_rating)
            rating_count = int(row.rating_count)

            weighted_rating = (
                (rating_count / (rating_count + minimum_votes))
                * average_rating
                + (
                    minimum_votes
                    / (rating_count + minimum_votes)
                )
                * overall_average
            )

            genre_preference = genre_preferences.get(
                row.genre,
                overall_average,
            )

            media_type_preference = media_type_preferences.get(
                row.media_type,
                overall_average,
            )

            genre_bonus = (
                genre_preference - overall_average
            ) * 0.2

            media_type_bonus = (
                media_type_preference - overall_average
            ) * 0.1

            final_score = (
                weighted_rating
                + genre_bonus
                + media_type_bonus
            )

            recommendations.append(
                {
                    "media_id": row.id,
                    "title": row.title,
                    "genre": row.genre,
                    "average_rating": average_rating,
                    "rating_count": rating_count,
                    "score": final_score,
                }
            )

        recommendations.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return recommendations[:limit]