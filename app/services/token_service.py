import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError

from app.core.config import get_settings
from app.db import User
from app.db.crud import UserCrud
from app.services import RedisClient
from app.services.redis_service import RedisTokenService
from app.utils.enums import TokenType

settings = get_settings()


class TokenService:
    """Service for creating and verifying JWT tokens."""

    def __init__(
        self,
        user_crud: UserCrud,
        redis_token_service: RedisTokenService,
        secret_key: str = settings.SECRET_KEY,
        algorithm: str = settings.ALGORITHM,
    ) -> None:
        """Initialize TokenService.

        Args:
            user_crud (UserCrud): CRUD service for user.
            redis_token_service (RedisClient): Redis token service.
            secret_key (str): Secret key for JWT encoding/decoding.
            algorithm (str): Algorithm to use for JWT.
        """
        self.user_crud = user_crud
        self.redis_token_service = redis_token_service
        self.secret_key = secret_key
        self.algorithm = algorithm

    async def create_tokens(self, user: User) -> Dict[str, str]:
        """Create new tokens for a user.

        Args:
            user: User to create tokens for.

        Returns:
            Dict[str, str]: Dictionary of tokens.
        """
        access_token = self.create_access_token(user.id, user.email)
        refresh_token = self.create_refresh_token(user.id, user.email)

        return {
            TokenType.ACCESS.prefix: access_token,
            TokenType.REFRESH.prefix: refresh_token,
        }

    def _create_token(
        self,
        user_id: int,
        email: str,
        token_type: str,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Internal method to create a JWT token.

        Args:
            user_id (int): User ID.
            email (str): User email.
            token_type (str): Token type ('access' or 'refresh').
            expires_delta (timedelta | None): Optional expiration delta.

        Returns:
            str: Encoded JWT token.
        """
        expire = datetime.now(timezone.utc) + (
            expires_delta
            or (
                timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                if token_type == TokenType.ACCESS.value.prefix
                else timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            )
        )
        payload = {
            "sub": str(user_id),
            "email": email,
            "type": token_type,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": str(uuid.uuid4()),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_access_token(
        self,
        user_id: int,
        email: str,
        expires_delta: Optional[timedelta] = TokenType.ACCESS.value.ttl,
    ) -> str:
        """Create a JWT access token."""
        return self._create_token(
            user_id, email, TokenType.ACCESS.value.prefix, expires_delta
        )

    def create_refresh_token(
        self,
        user_id: int,
        email: str,
        expires_delta: Optional[timedelta] = TokenType.ACCESS.value.ttl,
    ) -> str:
        """Create a JWT refresh token."""
        return self._create_token(
            user_id, email, TokenType.REFRESH.value.prefix, expires_delta
        )

    def decode_token(self, token: str) -> dict:
        """Decode and validate a JWT token (with expiration)."""
        return self._decode_token(token, verify_expiration=True)

    def decode_token_without_verify(self, token: str) -> dict:
        """Decode JWT token without validating expiration."""
        return self._decode_token(token, verify_expiration=False)

    def _decode_token(self, token: str, verify_expiration: bool = True) -> dict:
        """Internal method to decode JWT with optional expiration verification.

        Args:
            token (str): JWT token.
            verify_expiration (bool): Whether to verify expiration or not.

        Returns:
            dict: Decoded token payload.

        Raises:
            ValueError: If decoding fails or token is invalid.
        """
        try:
            return jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": verify_expiration},
            )
        except ExpiredSignatureError:
            raise ValueError("Token has expired.")
        except JWTError as exc:
            raise ValueError(f"Invalid token format: {str(exc)}")

    async def refresh_tokens(self, user_id: int) -> Dict[str, str]:
        """Refresh access and refresh tokens.

        Args:
            user_id: User identifier.

        Returns:
            Dict[str, str]: Access and refresh tokens.
        """
        user = await self.user_crud.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user.email} not found.",
            )
        await self.clear_tokens(user.email)
        return await self.create_tokens(user)

    async def clear_tokens(self, email: str) -> None:
        """Clear all access tokens.

        Args:
            email: Email address of user.
        """
        await self.redis_token_service.delete_access_token(email)
        await self.redis_token_service.delete_refresh_token(email)

    def extract_user_id_and_email(self, payload: Dict[str, Any]) -> tuple[int, str]:
        """Extract user ID and email from token payload.

        Args:
            payload (dict): Decoded token payload.

        Returns:
            tuple[int, str]: User ID and email.

        Raises:
            ValueError: If required claims are missing.
        """
        try:
            user_id = int(payload["sub"])
            email = payload["email"]
        except (KeyError, ValueError) as e:
            raise ValueError("Invalid token payload structure") from e
        return user_id, email

    @staticmethod
    async def generate_confirmation_code() -> str:
        """Generate a unique confirmation code.

        Returns:
            str: Generated confirmation code.
        """
        return str(uuid.uuid4())


class TokenValidator:
    """Service for validating tokens and interacting with Redis."""

    def __init__(self, token_service: TokenService) -> None:
        self.token_service = token_service

    async def _validate_token(
        self, token: str, expected_type: str
    ) -> tuple[bool, Optional[int], Optional[str]]:
        """Standalone check of access token.

        Args:
            token (str): JWT access token.
            expected_type (str): Expected token type.

        Returns:
            tuple: (is_expired, user_id, email)
        """

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is required.",
            )

        try:
            payload = self.token_service.decode_token(token)
            self.validate_token_type(payload, expected_type)
            user_id, email = self.token_service.extract_user_id_and_email(payload)
            return False, user_id, email

        except ValueError as e:
            if "expired" in str(e).lower():
                payload = self.token_service.decode_token_without_verify(token)
                self.validate_token_type(payload, expected_type)
                user_id, email = self.token_service.extract_user_id_and_email(payload)
                return True, user_id, email
            return False, None, None

    async def validate_access_token(
        self, token: str
    ) -> tuple[bool, Optional[int], Optional[str]]:
        return await self._validate_token(token, TokenType.ACCESS.prefix)

    async def validate_refresh_token(
        self, token: str
    ) -> tuple[bool, Optional[int], Optional[str]]:
        return await self._validate_token(token, TokenType.REFRESH.prefix)

    def validate_token_type(self, payload: Dict[str, Any], expected_type: str) -> None:
        """Validate the token type.

        Args:
            payload (dict): Decoded token payload.
            expected_type (str): Expected token type ('access' or 'refresh').

        Raises:
            ValueError: If token type does not match.
        """
        if payload.get("type") != expected_type:
            raise ValueError(f"Token type mismatch. Expected {expected_type}.")
