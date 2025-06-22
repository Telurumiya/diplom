from typing import Optional

from redis.asyncio import Redis
from redis.asyncio.connection import ConnectionPool

from app.core.config import get_settings

settings = get_settings()


class AsyncRedisClient:
    """Async Redis Client."""

    _pool: Optional[ConnectionPool] = None
    _client: Optional[Redis] = None

    @classmethod
    async def get_instance(cls) -> Redis:
        """Get or create async Redis client instance.

        Returns:
            Redis: Asynchronous Redis Client.
        """
        if cls._client is None:
            cls._pool = ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True,
            )
            cls._client = Redis(connection_pool=cls._pool)
        return cls._client

    @classmethod
    async def close(cls) -> None:
        """Closes the connection to Redis."""
        if cls._client is not None:
            await cls._client.aclose()
            cls._client = None
        if cls._pool is not None:
            await cls._pool.aclose()
            cls._pool = None


async def get_redis() -> Redis:
    """Dependency for getting an asynchronous Redis client.

    Returns:
        Redis: Asynchronous Redis Client.
    """
    return Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True,
    )
