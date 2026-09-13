from abc import ABC, abstractmethod


class ReviewObserver(ABC):

    @abstractmethod
    async def update(
        self,
        user_id: int,
        media_id: int,
    ) -> None:
        pass