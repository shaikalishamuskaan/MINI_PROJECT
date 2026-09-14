from textual.app import App, ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Footer, Header, Label, Button, Input

from sqlalchemy.exc import IntegrityError

from app.auth import AuthService
from app.session import Session
from app.recommendation import RecommendationEngine
from app.db import AsyncSessionLocal, create_tables
from app.cache import CacheService
from app.bulk import process_bulk_reviews

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
    UserService,
)

from app.observers.notification import NotificationObserver


class MediaReviewApp(App):
    """Textual UI for the Media Review System."""

    TITLE = "Media Review System"

    CSS = """
    #controls {
        height: 55%;
        padding: 1;
        overflow-y: auto;
    }

    #output {
        height: 45%;
        border: solid white;
        padding: 1;
        overflow-y: auto;
    }

    #user-status {
        margin: 1;
    }
    """

    # =========================================================
    # UI
    # =========================================================

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="controls"):

            yield Label(
                "Welcome to Media Review System!"
            )

            # -------------------------------------------------
            # AUTHENTICATION
            # -------------------------------------------------

            yield Label(
                "Not logged in",
                id="user-status",
            )

            yield Input(
                placeholder="Username",
                id="login-username",
            )

            yield Input(
                placeholder="Password",
                password=True,
                id="login-password",
            )

            yield Button(
                "Login",
                id="login",
            )

            yield Button(
                "Logout",
                id="logout",
            )

            # -------------------------------------------------
            # USER MANAGEMENT
            # -------------------------------------------------

            yield Input(
                placeholder="New username",
                id="new-username",
            )

            yield Input(
                placeholder="New password",
                password=True,
                id="new-password",
            )

            yield Button(
                "Create User",
                id="create-user",
            )

            # -------------------------------------------------
            # MEDIA MANAGEMENT
            # -------------------------------------------------

            yield Input(
                placeholder="Media title",
                id="media-title",
            )

            yield Input(
                placeholder="Type: movie / web_show / song",
                id="media-type",
            )

            yield Input(
                placeholder="Genre",
                id="media-genre",
            )

            yield Input(
                placeholder="Release year",
                id="media-year",
            )

            yield Button(
                "Add Media",
                id="add-media",
            )

            yield Button(
                "List Media",
                id="list-media",
            )

            # -------------------------------------------------
            # SEARCH
            # -------------------------------------------------

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

            # -------------------------------------------------
            # REVIEWS
            # -------------------------------------------------

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

            yield Input(
                placeholder="Media ID to view reviews",
                id="view-review-media-id",
            )

            yield Button(
                "View Reviews",
                id="view-reviews",
            )

            # -------------------------------------------------
            # FAVORITES
            # -------------------------------------------------

            yield Input(
                placeholder="Media ID to favorite",
                id="favorite-media-id",
            )

            yield Button(
                "Add Favorite",
                id="add-favorite",
            )

            yield Button(
                "Favorites",
                id="favorites",
            )

            # -------------------------------------------------
            # RECOMMENDATIONS
            # -------------------------------------------------

            yield Button(
                "Recommendations",
                id="recommend",
            )

            # -------------------------------------------------
            # NOTIFICATIONS
            # -------------------------------------------------

            yield Button(
                "Notifications",
                id="notifications",
            )

            # -------------------------------------------------
            # BULK REVIEWS
            # -------------------------------------------------

            yield Input(
                placeholder="CSV path, e.g. data/reviews.csv",
                id="bulk-file",
            )

            yield Button(
                "Import Bulk Reviews",
                id="bulk-review",
            )

        with VerticalScroll(id="output"):
            yield Label(
                "Login to use user-specific features."
            )

        yield Footer()

    # =========================================================
    # DISPLAY HELPERS
    # =========================================================

    async def clear_output(self) -> VerticalScroll:

        output = self.query_one(
            "#output",
            VerticalScroll,
        )

        await output.remove_children()

        return output

    def clear_login_inputs(self) -> None:

        self.query_one(
            "#login-username",
            Input,
        ).value = ""

        self.query_one(
            "#login-password",
            Input,
        ).value = ""

    def clear_user_inputs(self) -> None:

        self.query_one(
            "#new-username",
            Input,
        ).value = ""

        self.query_one(
            "#new-password",
            Input,
        ).value = ""

    def clear_media_inputs(self) -> None:

        self.query_one(
            "#media-title",
            Input,
        ).value = ""

        self.query_one(
            "#media-type",
            Input,
        ).value = ""

        self.query_one(
            "#media-genre",
            Input,
        ).value = ""

        self.query_one(
            "#media-year",
            Input,
        ).value = ""

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

    def update_user_status(self) -> None:

        status = self.query_one(
            "#user-status",
            Label,
        )

        if self.session.is_authenticated:

            status.update(
                f"Logged in as: {self.session.username}"
            )

        else:

            status.update(
                "Not logged in"
            )

    # =========================================================
    # AUTHENTICATION
    # =========================================================

    async def login_user(
        self,
        username: str,
        password: str,
    ) -> bool:

        try:

            user = await self.auth_service.login(
                username,
                password,
            )

            self.session.login(user)

            self.update_user_status()

            return True

        except ValueError:

            return False

    # =========================================================
    # BUTTON HANDLER
    # =========================================================

    async def on_button_pressed(
        self,
        event: Button.Pressed,
    ) -> None:

        # =====================================================
        # LOGIN
        # =====================================================

        if event.button.id == "login":

            output = await self.clear_output()

            username_input = self.query_one(
                "#login-username",
                Input,
            )

            password_input = self.query_one(
                "#login-password",
                Input,
            )

            username = username_input.value.strip()
            password = password_input.value

            if not username:

                output.mount(
                    Label(
                        "Please enter your username."
                    )
                )

                return

            if not password:

                output.mount(
                    Label(
                        "Please enter your password."
                    )
                )

                return

            success = await self.login_user(
                username,
                password,
            )

            if success:

                output.mount(
                    Label(
                        f"Login successful! "
                        f"Welcome, {self.session.username}."
                    )
                )

                self.clear_login_inputs()

            else:

                output.mount(
                    Label(
                        "Login failed: "
                        "Invalid username or password."
                    )
                )

            return

        # =====================================================
        # LOGOUT
        # =====================================================

        elif event.button.id == "logout":

            output = await self.clear_output()

            if not self.session.is_authenticated:

                output.mount(
                    Label(
                        "No user is currently logged in."
                    )
                )

                return

            username = self.session.username

            self.session.logout()

            self.update_user_status()

            output.mount(
                Label(
                    f"{username} logged out successfully."
                )
            )

            return

        # =====================================================
        # CREATE USER
        # =====================================================

        elif event.button.id == "create-user":

            output = await self.clear_output()

            username_input = self.query_one(
                "#new-username",
                Input,
            )

            password_input = self.query_one(
                "#new-password",
                Input,
            )

            username = username_input.value.strip()
            password = password_input.value

            try:

                user = await self.user_service.create_user(
                    username=username,
                    password=password,
                )

                output.mount(
                    Label(
                        "User created successfully! "
                        f"User ID: {user.id}"
                    )
                )

                self.clear_user_inputs()

            except IntegrityError:

                await self.db_session.rollback()

                output.mount(
                    Label(
                        "Error: Username already exists."
                    )
                )

            except (ValueError, TypeError) as error:

                output.mount(
                    Label(
                        f"Error: {error}"
                    )
                )

            return

        # =====================================================
        # ADD MEDIA
        # =====================================================

        elif event.button.id == "add-media":

            output = await self.clear_output()

            title_input = self.query_one(
                "#media-title",
                Input,
            )

            type_input = self.query_one(
                "#media-type",
                Input,
            )

            genre_input = self.query_one(
                "#media-genre",
                Input,
            )

            year_input = self.query_one(
                "#media-year",
                Input,
            )

            try:

                title = title_input.value.strip()
                media_type = type_input.value.strip()
                genre = genre_input.value.strip()
                year_text = year_input.value.strip()

                if not title:
                    raise ValueError(
                        "Please enter a media title."
                    )

                if not media_type:
                    raise ValueError(
                        "Please enter a media type."
                    )

                if not genre:
                    raise ValueError(
                        "Please enter a genre."
                    )

                if not year_text:
                    raise ValueError(
                        "Please enter a release year."
                    )

                release_year = int(year_text)

                media = await self.media_service.create_media(
                    title=title,
                    media_type=media_type,
                    genre=genre,
                    release_year=release_year,
                )

                output.mount(
                    Label(
                        "Media added successfully! "
                        f"Media ID: {media.id}"
                    )
                )

                self.clear_media_inputs()

            except IntegrityError:

                await self.db_session.rollback()

                output.mount(
                    Label(
                        "Error: Media could not be added."
                    )
                )

            except (ValueError, TypeError) as error:

                output.mount(
                    Label(
                        f"Error: {error}"
                    )
                )

            return

        # =====================================================
        # LIST MEDIA
        # =====================================================

        elif event.button.id == "list-media":

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

            output.scroll_home(
                animate=False
            )

        # =====================================================
        # SEARCH MEDIA
        # =====================================================

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
                Label(
                    "----- SEARCH RESULTS -----"
                )
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

            output.scroll_home(
                animate=False
            )

            search_input.value = ""

        # =====================================================
        # TOP RATED
        # =====================================================

        elif event.button.id == "top-rated":

            output = await self.clear_output()

            top_media = (
                await self.review_service.get_top_rated()
            )

            if not top_media:

                output.mount(
                    Label(
                        "No rated media found."
                    )
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

            output.scroll_home(
                animate=False
            )

        # =====================================================
        # ADD REVIEW
        # =====================================================

        elif event.button.id == "add-review":

            output = await self.clear_output()

            if not self.session.is_authenticated:

                output.mount(
                    Label(
                        "Please login first."
                    )
                )

                return

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

                media_id = int(
                    media_id_text
                )

                rating = int(
                    rating_text
                )

                review = (
                    await self.review_service
                    .create_review(
                        self.session.user_id,
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

                await self.db_session.rollback()

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

        # =====================================================
        # VIEW REVIEWS
        # =====================================================

        elif event.button.id == "view-reviews":

            output = await self.clear_output()

            media_id_input = self.query_one(
                "#view-review-media-id",
                Input,
            )

            media_id_text = (
                media_id_input.value.strip()
            )

            if not media_id_text:

                output.mount(
                    Label(
                        "Please enter a Media ID."
                    )
                )

                return

            try:

                media_id = int(
                    media_id_text
                )

                reviews = (
                    await self.review_service
                    .get_reviews(media_id)
                )

                if not reviews:

                    output.mount(
                        Label(
                            "No reviews found."
                        )
                    )

                    return

                output.mount(
                    Label(
                        "----- REVIEWS -----"
                    )
                )

                for review in reviews:

                    output.mount(
                        Label(
                            f"Review ID: {review.id} | "
                            f"User ID: {review.user_id} | "
                            f"Rating: {review.rating} | "
                            f"Comment: {review.comment}"
                        )
                    )

            except (ValueError, TypeError) as error:

                output.mount(
                    Label(
                        f"Error: {error}"
                    )
                )

        # =====================================================
        # ADD FAVORITE
        # =====================================================

        elif event.button.id == "add-favorite":

            output = await self.clear_output()

            if not self.session.is_authenticated:

                output.mount(
                    Label(
                        "Please login first."
                    )
                )

                return

            media_id_input = self.query_one(
                "#favorite-media-id",
                Input,
            )

            media_id_text = (
                media_id_input.value.strip()
            )

            if not media_id_text:

                output.mount(
                    Label(
                        "Please enter a Media ID."
                    )
                )

                return

            try:

                media_id = int(
                    media_id_text
                )

                favorite = (
                    await self.favorite_service
                    .add_favorite(
                        user_id=self.session.user_id,
                        media_id=media_id,
                    )
                )

                output.mount(
                    Label(
                        "Media added to favorites! "
                        f"Media ID: {favorite.media_id}"
                    )
                )

                media_id_input.value = ""

            except IntegrityError:

                await self.db_session.rollback()

                output.mount(
                    Label(
                        "Error: Media is already "
                        "in your favorites."
                    )
                )

            except (ValueError, TypeError) as error:

                output.mount(
                    Label(
                        f"Error: {error}"
                    )
                )

        # =====================================================
        # FAVORITES
        # =====================================================

        elif event.button.id == "favorites":

            output = await self.clear_output()

            if not self.session.is_authenticated:

                output.mount(
                    Label(
                        "Please login first."
                    )
                )

                return

            try:

                favorites = (
                    await self.favorite_service
                    .get_favorites(
                        self.session.user_id
                    )
                )

                if not favorites:

                    output.mount(
                        Label(
                            "No favorites found."
                        )
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

            except ValueError as error:

                output.mount(
                    Label(
                        f"Error: {error}"
                    )
                )

        # =====================================================
        # RECOMMENDATIONS
        # =====================================================

        elif event.button.id == "recommend":

            output = await self.clear_output()

            if not self.session.is_authenticated:

                output.mount(
                    Label(
                        "Please login first."
                    )
                )

                return

            recommendations = (
                await self.recommendation_engine
                .recommend(
                    user_id=self.session.user_id,
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

            output.scroll_home(
                animate=False
            )

        # =====================================================
        # NOTIFICATIONS
        # =====================================================

        elif event.button.id == "notifications":

            output = await self.clear_output()

            if not self.session.is_authenticated:

                output.mount(
                    Label(
                        "Please login first."
                    )
                )

                return

            notifications = (
                await self.notification_repository
                .get_notifications(
                    self.session.user_id
                )
            )

            if not notifications:

                output.mount(
                    Label(
                        "No notifications found."
                    )
                )

                return

            output.mount(
                Label(
                    "----- NOTIFICATIONS -----"
                )
            )

            for notification in notifications:

                status = (
                    "Read"
                    if notification.is_read
                    else "Unread"
                )

                output.mount(
                    Label(
                        f"{notification.id} | "
                        f"{status} | "
                        f"{notification.message}"
                    )
                )

        # =====================================================
        # BULK REVIEW
        # =====================================================

        elif event.button.id == "bulk-review":

            output = await self.clear_output()

            if not self.session.is_authenticated:

                output.mount(
                    Label(
                        "Please login first."
                    )
                )

                return

            file_input = self.query_one(
                "#bulk-file",
                Input,
            )

            file_name = (
                file_input.value.strip()
            )

            if not file_name:

                output.mount(
                    Label(
                        "Please enter the CSV file path."
                    )
                )

                return

            try:

                successful, failed = (
                    await process_bulk_reviews(
                        file_name=file_name,
                        user_id=self.session.user_id,
                        review_service=self.review_service,
                    )
                )

                output.mount(
                    Label(
                        "Bulk review processing completed."
                    )
                )

                output.mount(
                    Label(
                        f"Successful: {successful}"
                    )
                )

                output.mount(
                    Label(
                        f"Failed: {failed}"
                    )
                )

                file_input.value = ""

            except FileNotFoundError:

                output.mount(
                    Label(
                        "Error: Review file not found."
                    )
                )

            except ValueError as error:

                output.mount(
                    Label(
                        f"Error: {error}"
                    )
                )

    # =========================================================
    # START APPLICATION
    # =========================================================

    async def on_mount(self) -> None:

        await create_tables()

        # -----------------------------------------------------
        # DATABASE SESSION
        # -----------------------------------------------------

        self.db_session = AsyncSessionLocal()

        # -----------------------------------------------------
        # AUTHENTICATION SESSION
        # -----------------------------------------------------

        self.session = Session()

        # -----------------------------------------------------
        # REPOSITORIES
        # -----------------------------------------------------

        self.user_repository = UserRepository(
            self.db_session
        )

        self.media_repository = MediaRepository(
            self.db_session
        )

        self.review_repository = ReviewRepository(
            self.db_session
        )

        self.favorite_repository = FavoriteRepository(
            self.db_session
        )

        self.notification_repository = (
            NotificationRepository(
                self.db_session
            )
        )

        # -----------------------------------------------------
        # REDIS CACHE
        # -----------------------------------------------------

        self.cache_service = CacheService()

        # -----------------------------------------------------
        # OBSERVER
        # -----------------------------------------------------

        self.notification_observer = (
            NotificationObserver(
                self.favorite_repository,
                self.notification_repository,
            )
        )

        # -----------------------------------------------------
        # SERVICES
        # -----------------------------------------------------

        self.user_service = UserService(
            self.user_repository
        )

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

        # -----------------------------------------------------
        # RECOMMENDATION ENGINE
        # -----------------------------------------------------

        self.recommendation_engine = (
            RecommendationEngine(
                self.review_repository,
                self.media_repository,
            )
        )

        # -----------------------------------------------------
        # AUTHENTICATION
        # -----------------------------------------------------

        self.auth_service = AuthService(
            self.user_repository
        )

    # =========================================================
    # CLOSE APPLICATION
    # =========================================================

    async def on_unmount(self) -> None:

        await self.cache_service.close()

        await self.db_session.close()


if __name__ == "__main__":

    app = MediaReviewApp()

    app.run()