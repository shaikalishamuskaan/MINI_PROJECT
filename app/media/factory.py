from app.media.base import BaseMedia
from app.media.movie import Movie
from app.media.song import Song
from app.media.web_show import WebShow


class MediaFactory:

    @staticmethod
    def create_media(
        media_type: str,
        title: str,
        genre: str,
        release_year: int,
    ) -> BaseMedia:

        if media_type == "movie":
            return Movie(title, genre, release_year)

        if media_type == "web_show":
            return WebShow(title, genre, release_year)

        if media_type == "song":
            return Song(title, genre, release_year)

        raise ValueError(
            "Media type must be movie, web_show, or song."
        )