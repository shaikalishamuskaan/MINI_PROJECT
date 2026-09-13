import json

import redis.asyncio as redis


class CacheService:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        ttl: int = 300,
    ):
        self.client = redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
        )
        self.ttl = ttl

    async def get(self, key: str):
        value = await self.client.get(key)

        if value is None:
            return None

        return json.loads(value)

    async def set(self, key: str, value):
        await self.client.set(
            key,
            json.dumps(value),
            ex=self.ttl,
        )

    async def delete(self, key: str):
        await self.client.delete(key)

    async def close(self):
        await self.client.aclose()