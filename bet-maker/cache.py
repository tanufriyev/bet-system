import json
from typing import Any, Optional

from redis import asyncio as redis_async


class RedisCache:
    def __init__(self, redis_url: str):
        self.redis = redis_async.from_url(redis_url, decode_responses=True)
        self.default_ttl = 60

    async def get(self, key: str) -> Optional[Any]:
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        await self.redis.set(
            key,
            json.dumps(value),
            ex=ttl or self.default_ttl
        )

    async def delete(self, key: str) -> None:
        await self.redis.delete(key)

    async def close(self) -> None:
        await self.redis.close()

    async def get_info(self):
        return await self.redis.info()
