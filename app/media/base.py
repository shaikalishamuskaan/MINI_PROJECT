from abc import ABC


class BaseMedia(ABC):
    def __init__(
        self,
        title: str,
        genre: str,
        release_year: int,
    ):
        self.title = title
        self.genre = genre
        self.release_year = release_year

    def __str__(self) -> str:
        return f"{self.title} ({self.release_year})"