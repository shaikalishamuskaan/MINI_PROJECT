import asyncio

from app.db import AsyncSessionLocal
from app.repo import MediaRepository
from app.services import MediaService


async def main():
    async with AsyncSessionLocal() as session:
        repository = MediaRepository(session)
        service = MediaService(repository)

        media_list = await service.get_all_media()

        print("MEDIA COUNT:", len(media_list))

        for media in media_list:
            print(
                media.id,
                media.title,
                media.media_type,
                media.genre,
                media.release_year,
            )


asyncio.run(main())