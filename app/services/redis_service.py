from __future__ import annotations

import json
from datetime import timedelta
from typing import Any, Optional, Union

from pydantic import EmailStr
from redis import RedisError
from redis.asyncio import Redis

from app.core.config import get_settings
from app.core.exceptions import (
    CacheError,
    CorruptedSignupDataError,
    SignupCodeExistsError,
    SignupCodeNotFoundError,
    SignupDataCorruptedError,
    SignupInvalidConfirmationCodeError,
)
from app.core.logger import app_logger
from app.schemas.user import UserCreate
from app.utils.enums import TokenType


class RedisClient:
    """Base service for managing Redis operations."""

    def __init__(self, redis: Redis):
        """Initialize RedisService with Redis client.

        Args:
            redis: Async Redis client instance.
        """
        self._client = redis

    async def setex(self, key: str, expire_time: timedelta, value: Any) -> None:
        """Set key with expiration time.

        Args:
            key: Redis key.
            expire_time: Time to live.
            value: Value to store.

        Raises:
            CacheError: If Redis operation fails.
        """
        try:
            await self._client.setex(key, expire_time, value)
        except RedisError as e:
            app_logger.error(f"Failed to set Redis key {key} with expiration: {str(e)}")
            raise CacheError(detail=f"Failed to set cache: {str(e)}")

    async def set(self, key: str, value: Any, ex: Optional[timedelta] = None) -> None:
        """Set key with optional expiration.

        Args:
            key: Redis key.
            value: Value to store.
            ex: Optional time to live.

        Raises:
            CacheError: If Redis operation fails.
        """
        try:
            await self._client.set(key, value, ex=ex)
        except RedisError as e:
            app_logger.error(f"Failed to set Redis key {key}: {str(e)}")
            raise CacheError(detail=f"Failed to set cache: {str(e)}")

    async def get(self, key: str) -> Optional[Any]:
        """Get value by key.

        Args:
            key: Redis key.

        Returns:
            Stored value or None if not found.

        Raises:
            CacheError: If Redis operation fails.
        """
        try:
            return await self._client.get(key)
        except RedisError as e:
            app_logger.error(f"Failed to get Redis key {key}: {str(e)}")
            raise CacheError(detail=f"Failed to get cache: {str(e)}")

    async def delete(self, key: str) -> None:
        """Delete key.

        Args:
            key: Redis key.

        Raises:
            CacheError: If Redis operation fails.
        """
        try:
            await self._client.delete(key)
        except RedisError as e:
            app_logger.error(f"Failed to delete Redis key {key}: {str(e)}")
            raise CacheError(detail=f"Failed to delete cache: {str(e)}")

    async def exists(self, key: str) -> bool:
        """Check if key exists.

        Args:
            key: Redis key.

        Returns:
            True if key exists, False otherwise.

        Raises:
            CacheError: If Redis operation fails.
        """
        try:
            return bool(await self._client.exists(key))
        except RedisError as e:
            app_logger.error(f"Failed to check Redis key {key}: {str(e)}")
            raise CacheError(detail=f"Failed to check cache: {str(e)}")

    async def pipeline(self):
        """Get Redis pipeline for batch operations.

        Returns:
            Redis pipeline.

        Raises:
            CacheError: If Redis operation fails.
        """
        try:
            return self._client.pipeline()
        except RedisError as e:
            app_logger.error(f"Failed to create Redis pipeline: {str(e)}")
            raise CacheError(detail=f"Failed to create pipeline: {str(e)}")

    async def close(self) -> None:
        """Close Redis connection.

        Raises:
            CacheError: If Redis operation fails.
        """
        try:
            await self._client.close()
        except RedisError as e:
            app_logger.error(f"Failed to close Redis connection: {str(e)}")
            raise CacheError(detail=f"Failed to close connection: {str(e)}")


class RedisTokenService:
    """Service for managing access and refresh tokens via Redis."""

    def __init__(self, redis_client: RedisClient) -> None:
        """Initialize RedisTokenService with Redis client.

        Args:
            redis_client: Redis client instance.
        """
        self.redis = redis_client
        self.settings = get_settings()

    async def store_signup_code(
        self,
        user: UserCreate,
        code: str,
        expire: timedelta = TokenType.EMAIL_VERIFY.value.ttl,
    ):
        """Store signup confirmation code in Redis.

        Args:
            user: User creation data.
            code: Confirmation code.
            expire: Time to live for the stored code.

        Raises:
            SignupCodeExistsError: If code already exists.
            CacheError: If Redis operation fails.
        """
        key = f"{TokenType.EMAIL_VERIFY.prefix}:{user.email}"

        try:
            if await self.redis.exists(key):
                raise SignupCodeExistsError()

            payload = {
                "user_data": user.model_dump(exclude_unset=True),
                "code": code,
            }

            await self.redis.setex(key, expire, json.dumps(payload))
            app_logger.info(f"Stored signup code for user {user.email}")
        except RedisError as e:
            app_logger.error(f"Failed to store signup code for {user.email}: {str(e)}")
            raise CacheError(detail=f"Failed to store signup code: {str(e)}")

    async def get_signup_data(
        self, email: Union[EmailStr, str], code: str
    ) -> Optional[dict]:
        """Retrieve signup data by confirmation code from Redis.

        Args:
            email: User email.
            code: Confirmation code.

        Returns:
            Stored signup data or None if not found.

        Raises:
            SignupCodeNotFoundError: If code not found.
            SignupInvalidConfirmationCodeError: If code is invalid.
            SignupDataCorruptedError: If data is corrupted.
            CacheError: If Redis operation fails.
        """
        key = f"{TokenType.EMAIL_VERIFY.prefix}:{email}"

        try:
            data_raw = await self.redis.get(key)
            if not data_raw:
                raise SignupCodeNotFoundError()

            try:
                data = json.loads(data_raw)
            except json.JSONDecodeError:
                app_logger.error(f"Corrupted signup data for {email}")
                raise CorruptedSignupDataError()

            if data.get("code") != code:
                app_logger.warning(f"Invalid confirmation code for {email}")
                raise SignupInvalidConfirmationCodeError()

            user_data = data.get("user_data")
            if not user_data:
                app_logger.error(f"Missing user data for {email}")
                raise SignupDataCorruptedError()

            return user_data
        except RedisError as e:
            app_logger.error(f"Failed to get signup data for {email}: {str(e)}")
            raise CacheError(detail=f"Failed to get signup data: {str(e)}")

    async def delete_signup_code(self, email: Union[EmailStr, str]) -> None:
        """Delete signup confirmation email from Redis.

        Args:
            email: User email.

        Raises:
            CacheError: If Redis operation fails.
        """
        try:
            await self.redis.delete(f"{TokenType.EMAIL_VERIFY.value.prefix}:{email}")
            app_logger.info(f"Deleted signup code for {email}")
        except RedisError as e:
            app_logger.error(f"Failed to delete signup code for {email}: {str(e)}")
            raise CacheError(detail=f"Failed to delete signup code: {str(e)}")

    async def _store_token(
        self, token_type: TokenType, identifier: Union[EmailStr, str], token: str
    ) -> None:
        """Store token in Redis.

        Args:
            token_type: JWT token type.
            identifier: User email or username.
            token: Token value.

        Raises:
            CacheError: If Redis operation fails.
        """
        try:
            await self.redis.setex(
                f"{token_type.prefix}:{identifier}", token_type.ttl, token
            )
        except RedisError as e:
            app_logger.error(
                f"Failed to store {token_type.value} token for {identifier}: {str(e)}"
            )
            raise CacheError(detail=f"Failed to store token: {str(e)}")

    async def _get_token(
        self, token_type: TokenType, identifier: Union[EmailStr, str]
    ) -> Optional[str]:
        """Get token from Redis.

        Args:
            token_type: Type of jwt token.
            identifier: User email or username.

        Returns:
            Token value if exists, otherwise None.

        Raises:
            CacheError: If Redis operation fails.
        """
        try:
            return await self.redis.get(f"{token_type.prefix}:{identifier}")
        except RedisError as e:
            app_logger.error(
                f"Failed to get {token_type.value} token for {identifier}: {str(e)}"
            )
            raise CacheError(detail=f"Failed to get token: {str(e)}")

    async def _delete_token(
        self, token_type: TokenType, identifier: Union[EmailStr, str]
    ) -> None:
        """Delete token from Redis.

        Args:
            token_type: Type of jwt token.
            identifier: User email or username.

        Raises:
            CacheError: If Redis operation fails.
        """
        try:
            await self.redis.delete(f"{token_type.prefix}:{identifier}")
            app_logger.info(f"Deleted {token_type.value} token for {identifier}")
        except RedisError as e:
            app_logger.error(
                f"Failed to delete {token_type.value} token for {identifier}: {str(e)}"
            )
            raise CacheError(detail=f"Failed to delete token: {str(e)}")

    # Token-specific methods with proper error handling
    async def store_access_token(
        self, identifier: Union[EmailStr, str], token: str
    ) -> None:
        """Store access token in Redis.

        Args:
            identifier: User email address or username.
            token: Access token for storing.

        Raises:
            CacheError: If Redis operation fails.
        """
        await self._store_token(TokenType.ACCESS, identifier, token)

    async def store_refresh_token(
        self, identifier: Union[EmailStr, str], token: str
    ) -> None:
        """Store refresh token in Redis.

        Args:
            identifier: User email address or username.
            token: Refresh token for storing.

        Raises:
            CacheError: If Redis operation fails.
        """
        await self._store_token(TokenType.REFRESH, identifier, token)

    async def get_access_token(self, identifier: Union[EmailStr, str]) -> Optional[str]:
        """Retrieve access token from Redis.

        Args:
            identifier: User email address or username.

        Returns:
            Stored access token or None if not found.

        Raises:
            CacheError: If Redis operation fails.
        """
        return await self._get_token(TokenType.ACCESS, identifier)

    async def get_refresh_token(
        self, identifier: Union[EmailStr, str]
    ) -> Optional[str]:
        """Retrieve refresh token from Redis.

        Args:
            identifier: User email address or username.

        Returns:
            Stored refresh token or None if not found.

        Raises:
            CacheError: If Redis operation fails.
        """
        return await self._get_token(TokenType.REFRESH, identifier)

    async def delete_access_token(self, identifier: Union[EmailStr, str]) -> None:
        """Delete access token from Redis.

        Args:
            identifier: User email address or username.

        Raises:
            CacheError: If Redis operation fails.
        """
        await self._delete_token(TokenType.ACCESS, identifier)

    async def delete_refresh_token(self, identifier: Union[EmailStr, str]) -> None:
        """Delete refresh token from Redis.

        Args:
            identifier: User email address or username.

        Raises:
            CacheError: If Redis operation fails.
        """
        await self._delete_token(TokenType.REFRESH, identifier)


__all__ = ["RedisClient", "RedisTokenService"]
