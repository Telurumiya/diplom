"""JWT Token Authentication and Validity Utilities."""

from __future__ import annotations

from typing import Dict

from fastapi import Request, Response, WebSocket, status
from passlib.context import CryptContext

from app.core.exceptions import (
    AccessTokenRevokedError,
    InvalidAccessTokenError,
    InvalidRefreshTokenError,
    MissingTokensError,
    PasswordIncorrectError,
    RefreshTokenExpiredError,
    SignupDataNotFoundError,
    SignupEmailNotFoundError,
    UserNotFoundError,
)
from app.core.logger import app_logger
from app.db.crud import UserCrud
from app.db.models.user import User
from app.services.redis_service import RedisTokenService
from app.services.token_service import TokenService, TokenValidator
from app.utils.enums import TokenType


class PasswordService:
    """Service for hashing and verifying passwords."""

    def __init__(
        self, schemes: list[str] | None = None, deprecated: str = "auto"
    ) -> None:
        """
        Initialize PasswordService.

        Args:
            schemes (list[str] | None): List of hashing schemes to use.
            deprecated (str): Deprecation policy.
        """
        self.context = CryptContext(
            schemes=schemes or ["bcrypt"], deprecated=deprecated
        )

    def hash_password(self, password: str) -> str:
        """
        Hash a plain password.

        Args:
            password (str): Plain password.

        Returns:
            str: Hashed password.
        """
        return self.context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against a hashed password.

        Args:
            plain_password (str): Plain password.
            hashed_password (str): Hashed password.

        Returns:
            bool: True if passwords match, False otherwise.
        """
        return self.context.verify(plain_password, hashed_password)


class AuthService:
    """Service for authentication."""

    def __init__(
        self,
        user_crud: UserCrud,
        password_service: PasswordService,
        token_service: TokenService,
        token_validator: TokenValidator,
        redis_token_service: RedisTokenService,
    ) -> None:
        self.user_crud = user_crud
        self.password_service = password_service
        self.token_service = token_service
        self.token_validator = token_validator
        self.rts = redis_token_service

    async def authenticate_user(self, identifier: str, password: str) -> User:
        """Authenticate a user with given identifier and password.

        Args:
            identifier: Identifier to authenticate.
            password: User's password.

        Returns:
            User: User object.
        """
        user = await self.user_crud.get_by_identifier(identifier)
        if not user:
            raise UserNotFoundError()
        if not self.password_service.verify_password(password, user.password):
            raise PasswordIncorrectError()
        return user

    async def validate_signup_data(self, user_data: dict) -> dict:
        """Validate user data from signup data.

        Args:
            user_data: Parsed user data.

        Returns:
            dict: Validated user data.

        Raises:
            SignupDataNotFoundError: If signup data is missing.
            SignupEmailNotFoundError: If signup email in user data is missing.
        """
        if not user_data:
            app_logger.warning("No user data in signup data")
            raise SignupDataNotFoundError()

        email = user_data.get("email")
        if not email:
            app_logger.warning("No email address in user data")
            raise SignupEmailNotFoundError()

        user_data["password"] = self.password_service.hash_password(
            user_data["password"]
        )
        return user_data

    async def handle_tokens(self, response: Response, user: User) -> Dict[str, str]:
        """Handle token creation, storage, and setting cookies.

        Args:
            response: FastAPI response to set cookies.
            user: User object.

        Returns:
            Dict[str, str]: Dictionary of tokens.
        """
        tokens = await self.token_service.create_tokens(user)

        await self.rts.store_access_token(
            user.email or user.username, tokens.get(TokenType.ACCESS.prefix)
        )
        await self.rts.store_refresh_token(
            user.email or user.username, tokens.get(TokenType.REFRESH.prefix)
        )
        await self.set_auth_cookies(response, tokens)
        return tokens

    async def set_auth_cookie(
        self, response: Response, token_type: TokenType, token: str
    ) -> None:
        """Set a token in the response cookie.

        Args:
            response: Response object to set the cookie in.
            token_type: Type of token to set (e.g., ACCESS, REFRESH).
            token: The token value to set in the cookie.
        """
        response.set_cookie(
            key=f"{token_type.prefix}",
            value=token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=int(token_type.ttl.total_seconds()),
        )

    async def set_auth_cookies(
        self, response: Response, tokens: Dict[str, str]
    ) -> None:
        """Set multiple tokens in the response cookie.

        Args:
            response: Response object to set the cookie in.
            tokens: Dictionary of token type and their values.
        """
        for prefix, token in tokens.items():
            token_type = next(
                (tt for tt in TokenType if tt.value.prefix == prefix), None
            )
            if token_type is None:
                continue

            await self.set_auth_cookie(response, token_type, token)

    async def _verify_user(self, request: Request, response: Response) -> User:
        """Verify access token, or refresh tokens if necessary.

        Args:
            request: Incoming HTTP request.
            response: HTTP response to set new cookies.

        Returns:
            User: Verified user.

        Raises:
            MissingTokensError: If access or refresh tokens are missing.
            AccessTokenRevokedError: If access token is revoked or expired.
            RefreshTokenExpiredError: If refresh token is revoked or expired.
            UserNotFoundError: If user does not exist.
            InvalidRefreshTokenError: If refresh token is invalid.
        """
        access_token = request.cookies.get(TokenType.ACCESS.prefix)
        refresh_token = request.cookies.get(TokenType.REFRESH.prefix)

        if not access_token or not refresh_token:
            raise MissingTokensError()

        is_access_expired, user_id, email = (
            await self.token_validator.validate_access_token(access_token)
        )

        cached_access_token = await self.rts.get_access_token(email)
        if cached_access_token is None:
            raise AccessTokenRevokedError()

        user = await self.user_crud.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        if not is_access_expired:
            return user

        is_refresh_expired, *_ = await self.token_validator.validate_refresh_token(
            refresh_token
        )

        if is_refresh_expired:
            raise RefreshTokenExpiredError()

        cached_token = await self.rts.get_refresh_token(email)
        if cached_token != refresh_token:
            raise InvalidRefreshTokenError()

        tokens = await self.handle_tokens(response, user)
        await self.set_auth_cookies(response, tokens)
        return user

    async def _verify_user_websocket(self, websocket: WebSocket) -> User:
        """Verify access and refresh token in WebSocket connection.

        Args:
            websocket: WebSocket connection.

        Returns:
            User: Verified user model object.

        Raises:
            MissingTokensError: If access or refresh tokens are missing.
            AccessTokenRevokedError: If access token is revoked or expired.
            RefreshTokenExpiredError: If refresh token is revoked or expired.
            UserNotFoundError: If user does not exist.
            InvalidRefreshTokenError: If refresh token is invalid.
        """
        access_token = websocket.cookies.get(TokenType.ACCESS.prefix)
        refresh_token = websocket.cookies.get(TokenType.REFRESH.prefix)

        if not access_token or not refresh_token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise MissingTokensError()

        is_access_expired, user_id, email = (
            await self.token_validator.validate_access_token(access_token)
        )

        cached_access_token = await self.rts.get_access_token(email)
        if cached_access_token is None:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise InvalidAccessTokenError()

        user = await self.user_crud.get_by_id(user_id)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise UserNotFoundError()

        if not is_access_expired:
            return user

        is_refresh_expired, *_ = await self.token_validator.validate_refresh_token(
            refresh_token
        )

        if is_refresh_expired:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise RefreshTokenExpiredError()

        cached_refresh_token = await self.rts.get_refresh_token(email)
        if cached_refresh_token != refresh_token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise InvalidRefreshTokenError()

        tokens = await self.token_service.refresh_tokens(user_id)
        await self.rts.store_access_token(
            user.email or user.username, tokens.get(TokenType.ACCESS.prefix)
        )
        await self.rts.store_refresh_token(
            user.email or user.username, tokens.get(TokenType.REFRESH.prefix)
        )

        await websocket.send_json(
            {
                "type": "token_refresh",
                "access_token": tokens.get(TokenType.ACCESS.value.prefix),
                "refresh_token": tokens.get(TokenType.REFRESH.value.prefix),
            }
        )

        websocket.state.access_token = tokens.get(TokenType.ACCESS.value.prefix)
        websocket.state.refresh_token = tokens.get(TokenType.REFRESH.value.prefix)
        return user

    async def logout(self, response: Response, user: User) -> None:
        """Log out user: clear tokens in Redis and delete cookies.

        Args:
            response: HTTP response to set new cookies.
            user: User object.
        """
        await self.token_service.clear_tokens(user.email)
        response.delete_cookie("access_token_cookie")
        response.delete_cookie("refresh_token_cookie")
