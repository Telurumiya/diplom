from typing import AsyncGenerator

from fastapi import Depends, Request, Response, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud import UserCrud
from app.db.database import get_async_session_context
from app.db.models.user import User
from app.db.redis import get_redis
from app.services.auth_service import (
    AuthService,
    PasswordService,
    TokenService,
    TokenValidator,
)
from app.services.document_service import DocumentService
from app.services.redis_service import RedisClient, RedisTokenService


async def get_async_session():
    """Provide an async database session for FastAPI dependencies.

    Yields:
        AsyncSession: A configured async SQLAlchemy session.
    """
    async with get_async_session_context() as session:
        yield session


async def get_redis_client() -> RedisClient:
    """Get RedisClient instance.

    Returns:
        RedisClient: Instance of RedisService.
    """
    return RedisClient(await get_redis())


async def get_redis_token_service() -> RedisTokenService:
    """Get RedisTokenService instance.

    Returns:
        RedisTokenService: Instance of RedisTokenService.
    """
    return RedisTokenService(await get_redis_client())


async def get_user_crud(db=Depends(get_async_session)) -> UserCrud:
    """Get User CRUD instance.

    Args:
        db: Database session instance.

    Returns:
        UserCrud: Instance of UserCrudService.
    """
    return UserCrud(db)


async def get_auth_service(
    redis_client=Depends(get_redis_client),
    user_crud=Depends(get_user_crud),
) -> AuthService:
    """Dependency for injecting AuthService.

    Args:
        redis_client: Redis client instance.
        user_crud: User CRUD instance.

    Returns:
        AuthService: Instance of AuthService.
    """
    redis_token_service = RedisTokenService(redis_client=redis_client)
    token_service = TokenService(user_crud, redis_token_service)
    password_service = PasswordService()
    token_validator = TokenValidator(token_service=token_service)

    return AuthService(
        user_crud=user_crud,
        password_service=password_service,
        token_service=token_service,
        token_validator=token_validator,
        redis_token_service=redis_token_service,
    )


async def verify_user(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Dependency to get currently authenticated user.

    Args:
        request: Request instance.
        response: Response instance.
        auth_service: AuthService instance

    Returns:
        User: User instance.
    """
    return await auth_service._verify_user(request, response)


async def verify_user_socket(
    websocket: WebSocket,
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Dependency for injecting AuthService.

    Args:
        websocket: WebSocket instance.
        auth_service: AuthService instance.

    Returns:
        User: User instance.
    """
    return await auth_service._verify_user_websocket(websocket)


async def get_token_validator(
    redis_token_service=Depends(get_redis_token_service),
    user_crud=Depends(get_user_crud),
) -> TokenValidator:
    """Dependency to get a TokenValidator instance.

    Args:
        redis_token_service: RedisTokenService instance.
        user_crud: User CRUD instance.

    Returns:
        TokenValidator: TokenValidator instance.
    """
    token_service = TokenService(user_crud, redis_token_service)
    return TokenValidator(token_service=token_service)


async def get_document_service(db=Depends(get_async_session)):
    return DocumentService(db=db)
