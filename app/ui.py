from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Footer, Header, Label, Button, Input
from sqlalchemy.exc import IntegrityError

from app.recommendation import RecommendationEngine
from app.db import AsyncSessionLocal, create_tables
from app.cache import CacheService

from app.repo import (
    FavoriteRepository,
    MediaRepository,
    ReviewRepository,
    UserRepository,
    NotificationRepository,
)

from app.services import (
    FavoriteService,
    MediaService,
    ReviewService,
)

from app.observers.notification import NotificationObserver


class MediaReviewApp(App):
    """Textual UI for the Media Review System."""

    TITLE = "Media Review System"

    CSS = """
    #controls {
        height: 50%;
        padding: 1;
        overflow-y: auto;
    }

    #output {
        height: 50%;
        border: solid white;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="controls"):
            yield Label("Welcome to Media Review System!")

            yield Button(
                "List Media",
                id="list-media",
            )

            yield Input(
                placeholder="Enter media title to search",
                id="search-input",
            )

            yield Button(
                "Search Media",
                id="search-media",
            )

            yield Button(
                "Top Rated",
                id="top-rated",
            )

            yield Input(
                placeholder="Media ID",
                id="review-media-id",
            )

            yield Input(
                placeholder="Rating (1-5)",
                id="review-rating",
            )

            yield Input(
                placeholder="Comment",
                id="review-comment",
            )

            yield Button(
                "Add Review",
                id="add-review",
            )

            yield Button(
                "Favorites",
                id="favorites",
            )

            yield Button(
                "Recommendations",
                id="recommend",
            )

        with VerticalScroll(id="output"):
            yield Label(
                "Results will appear here."
            )

        yield Footer()

    
    # DISPLAY RESULTS
    

    async def clear_output(self) -> VerticalScroll:

        output = self.query_one(
            "#output",
            VerticalScroll,
        )

        await output.remove_children()

        return output

    def clear_review_inputs(self) -> None:

        self.query_one(
            "#review-media-id",
            Input,
        ).value = ""

        self.query_one(
            "#review-rating",
            Input,
        ).value = ""

        self.query_one(
            "#review-comment",
            Input,
        ).value = ""

    
    # BUTTON HANDLER
    

    async def on_button_pressed(
        self,
        event: Button.Pressed,
    ) -> None:

        # LIST MEDIA

        if event.button.id == "list-media":

            output = await self.clear_output()

            media_list = (
                await self.media_service.get_all_media()
            )

            if not media_list:

                output.mount(
                    Label("No media found.")
                )

                return

            output.mount(
                Label("----- ALL MEDIA -----")
            )

            for media in media_list:

                output.mount(
                    Label(
                        f"{media.id} | "
                        f"{media.title} | "
                        f"{media.media_type} | "
                        f"{media.genre} | "
                        f"{media.release_year}"
                    )
                )

            output.scroll_home(animate=False)

        # SEARCH MEDIA

        elif event.button.id == "search-media":

            output = await self.clear_output()

            search_input = self.query_one(
                "#search-input",
                Input,
            )

            search_text = (
                search_input.value.strip()
            )

            if not search_text:

                output.mount(
                    Label(
                        "Please enter a title to search."
                    )
                )

                return

            media_list = (
                await self.media_service.search_media(
                    search_text
                )
            )

            if not media_list:

                output.mount(
                    Label(
                        "No matching media found."
                    )
                )

                return

            output.mount(
                Label("----- SEARCH RESULTS -----")
            )

            for media in media_list:

                output.mount(
                    Label(
                        f"{media.id} | "
                        f"{media.title} | "
                        f"{media.media_type} | "
                        f"{media.genre} | "
                        f"{media.release_year}"
                    )
                )

            output.scroll_home(animate=False)

            search_input.value = ""

        # TOP RATED

        elif event.button.id == "top-rated":

            output = await self.clear_output()

            top_media = (
                await self.review_service.get_top_rated()
            )

            if not top_media:

                output.mount(
                    Label("No rated media found.")
                )

                return

            output.mount(
                Label(
                    "----- TOP RATED MEDIA -----"
                )
            )

            for media, average_rating in top_media:

                output.mount(
                    Label(
                        f"{media.title} | "
                        f"Average Rating: "
                        f"{average_rating:.2f}"
                    )
                )

            output.scroll_home(animate=False)

        # FAVORITES

        elif event.button.id == "favorites":

            output = await self.clear_output()

            user_id = 1

            try:

                favorites = (
                    await self.favorite_service
                    .get_favorites(user_id)
                )

                if not favorites:

                    output.mount(
                        Label("No favorites found.")
                    )

                    return

                output.mount(
                    Label(
                        "----- YOUR FAVORITES -----"
                    )
                )

                for media in favorites:

                    output.mount(
                        Label(
                            f"{media.id} | "
                            f"{media.title} | "
                            f"{media.media_type} | "
                            f"{media.genre} | "
                            f"{media.release_year}"
                        )
                    )

                output.scroll_home(animate=False)

            except ValueError as error:

                output.mount(
                    Label(f"Error: {error}")
                )

        # ADD REVIEW

        elif event.button.id == "add-review":

            output = await self.clear_output()

            media_id_input = self.query_one(
                "#review-media-id",
                Input,
            )

            rating_input = self.query_one(
                "#review-rating",
                Input,
            )

            comment_input = self.query_one(
                "#review-comment",
                Input,
            )

            try:

                media_id_text = (
                    media_id_input.value.strip()
                )

                rating_text = (
                    rating_input.value.strip()
                )

                comment = (
                    comment_input.value.strip()
                )

                if not media_id_text:

                    raise ValueError(
                        "Please enter a Media ID."
                    )

                if not rating_text:

                    raise ValueError(
                        "Please enter a rating."
                    )

                media_id = int(media_id_text)
                rating = int(rating_text)

                review = (
                    await self.review_service
                    .create_review(
                        user_id=1,
                        media_id=media_id,
                        rating=rating,
                        comment=comment,
                    )
                )

                output.mount(
                    Label(
                        "Review submitted successfully! "
                        f"Review ID: {review.id}"
                    )
                )

                self.clear_review_inputs()

            except IntegrityError:

                await self.session.rollback()

                output.mount(
                    Label(
                        "Error: You have already "
                        "reviewed this media."
                    )
                )

            except (ValueError, TypeError) as error:

                output.mount(
                    Label(
                        f"Error: {error}"
                    )
                )

        # RECOMMENDATIONS

        elif event.button.id == "recommend":

            output = await self.clear_output()

            user_id = 1

            recommendations = (
                await self.recommendation_engine
                .recommend(
                    user_id=user_id,
                    limit=5,
                )
            )

            if not recommendations:

                output.mount(
                    Label(
                        "No recommendations available."
                    )
                )

                return

            output.mount(
                Label(
                    "----- RECOMMENDATIONS -----"
                )
            )

            for item in recommendations:

                output.mount(
                    Label(
                        f"{item['title']} | "
                        f"{item['genre']} | "
                        f"Average Rating: "
                        f"{item['average_rating']:.2f} | "
                        f"Score: "
                        f"{item['score']:.2f}"
                    )
                )

            output.scroll_home(animate=False)

    
    # START APPLICATION
    

    async def on_mount(self) -> None:

        await create_tables()

        self.session = AsyncSessionLocal()

        # REPOSITORIES

        self.user_repository = UserRepository(
            self.session
        )

        self.media_repository = MediaRepository(
            self.session
        )

        self.review_repository = ReviewRepository(
            self.session
        )

        self.favorite_repository = FavoriteRepository(
            self.session
        )

        self.notification_repository = (
            NotificationRepository(
                self.session
            )
        )

        # REDIS CACHE

        self.cache_service = CacheService()

        # OBSERVER

        self.notification_observer = (
            NotificationObserver(
                self.favorite_repository,
                self.notification_repository,
            )
        )

        # SERVICES

        self.media_service = MediaService(
            self.media_repository
        )

        self.review_service = ReviewService(
            self.review_repository,
            self.user_repository,
            self.media_repository,
            cache_service=self.cache_service,
            observers=[
                self.notification_observer
            ],
        )

        self.favorite_service = FavoriteService(
            self.favorite_repository,
            self.user_repository,
            self.media_repository,
        )

        # RECOMMENDATION ENGINE

        self.recommendation_engine = (
            RecommendationEngine(
                self.review_repository,
                self.media_repository,
            )
        )

    
    # CLOSE APPLICATION
    

    async def on_unmount(self) -> None:

        await self.cache_service.close()

        await self.session.close()


if __name__ == "__main__":

    app = MediaReviewApp()

    app.run()