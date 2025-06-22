"""Authenticate endpoint."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api.dependencies import (
    get_auth_service, get_redis_token_service, verify_user
)
from app.core.exceptions import (
    SignupException, AuthException, RepositoryException, DomainException,
    UserNotFoundError, PasswordIncorrectError, SignupCodeNotFoundError
)
from app.db.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.services.auth_service import AuthService
from app.services.celery_service import task_to_confirm_email
from app.services.redis_service import RedisTokenService
from app.utils.email_templates import EmailTemplateType
from app.utils.enums import TokenType

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent.parent / "static"))


@router.post("/signup")
async def signup(
    user: UserCreate,
    redis_service: RedisTokenService = Depends(get_redis_token_service),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    """Register new user and send confirmation email.

    Args:
        user: User creation data.
        redis_service: Redis token service.
        auth_service: AuthService for business logic.

    Raises:
        HTTPException: If email already exists.
    """
    try:
        await auth_service.user_crud.check_user_exists(user.email, user.username)

        key = f"{TokenType.EMAIL_VERIFY.prefix}:{user.email}"
        if await redis_service.redis.exists(key):
            raise HTTPException(
                status_code=400,
                detail="Письмо для подтверждения регистрации уже отправлено. Пожалуйста, проверьте почтовый ящик.",
            )

        confirmation_code = (
            await auth_service.token_service.generate_confirmation_code()
        )

        await redis_service.store_signup_code(user, confirmation_code)

        task_to_confirm_email.delay(
            email=user.email,
            template_type=EmailTemplateType.REGISTRATION_CONFIRMATION.value,
            confirmation_code=confirmation_code,
        )
    except SignupException as e:
        raise HTTPException(
            status_code=400,
            detail=e.default_detail,
        )


@router.get("/confirm-signup")
async def confirm_signup(
    request: Request,
    email: str = Query(...),
    code: str = Query(...),
    redis_service: RedisTokenService = Depends(get_redis_token_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Confirm signup by code from Redis.

    Args:
        request:
        email: User email from query parameters.
        code: Confirmation code from email.
        redis_service: Redis client.
        auth_service: AuthService for business logic.

    Raises:
        HTTPException: If validation fails or user already exists.
    """
    try:
        await auth_service.user_crud.check_user_exists(email)

        store_data = await redis_service.get_signup_data(email, code)
        user_data = await auth_service.validate_signup_data(store_data)

        await auth_service.user_crud.create_user(user_data)
        await redis_service.delete_signup_code(email)

        return RedirectResponse(url=request.url_for("confirm_success"))

    except (SignupCodeNotFoundError, RepositoryException, SignupException) as e:
        # Для ошибки используем явный URL с параметрами
        error_url = request.url_for("confirm_error").include_query_params(detail=str(e.detail))
        return RedirectResponse(url=error_url)


@router.get("/confirm-success")
async def confirm_success(request: Request):
    """Страница успешного подтверждения"""
    return templates.TemplateResponse("confirm_success.html", {"request": request})


@router.get("/confirm-error")
async def confirm_error(request: Request, detail: str = "Произошла ошибка"):
    """Страница ошибки подтверждения"""
    return templates.TemplateResponse("confirm_error.html", {
        "request": request,
        "error_detail": detail
    })


@router.post("/login")
async def login(
    data: UserLogin,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Authenticate user and set access/refresh tokens in cookies.

    Args:
        data: User login credentials.
        response: FastAPI response to set cookies.
        auth_service: AuthService instance.

    Raises:
        HTTPException: If authentication fails.
    """
    try:
        user = await auth_service.authenticate_user(
            identifier=data.identifier,
            password=data.password
        )

        tokens = await auth_service.handle_tokens(response, user)
        await auth_service.set_auth_cookies(response, tokens)

    except UserNotFoundError:
        raise HTTPException(
            status_code=401,
            detail="Пользователь с таким email/логином не найден"
        )
    except PasswordIncorrectError:
        raise HTTPException(
            status_code=401,
            detail="Неверный пароль"
        )
    except AuthException as e:
        raise HTTPException(
            status_code=400,
            detail=f"Ошибка входа: {str(e)}"
        )


@router.post("/logout")
async def logout(
    response: Response,
    user: User = Depends(verify_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Log out user.

    Args:
        response: FastAPI response to delete cookies.
        user: User login credentials.
        auth_service: TokenValidator instance.
    """
    try:
        await auth_service.logout(response, user)
    except DomainException as e:
        raise HTTPException(
            status_code=400,
            detail=e.detail
        )


@router.post("/refresh")
async def refresh(
    response: Response,
    user: User = Depends(verify_user),
    auth_service: AuthService = Depends(get_auth_service),
    redis_service: RedisTokenService = Depends(get_redis_token_service),
):
    """Force refresh tokens (if needed).

    Args:
        response: FastAPI response to set cookies.
        user: User login credentials.
        auth_service: AuthService instance.
        redis_service: Redis client.
    """
    try:
        tokens = await auth_service.token_service.refresh_tokens(user.id)
        await redis_service.store_access_token(
            user.email or user.username, tokens.get(TokenType.ACCESS.prefix)
        )
        await redis_service.store_refresh_token(
            user.email or user.username, tokens.get(TokenType.REFRESH.prefix)
        )
        await auth_service.set_auth_cookies(response, tokens)
        return tokens
    except AuthException as e:
        raise HTTPException(
            status_code=401,
            detail=e.detail
        )
    except RepositoryException as e:
        raise HTTPException(
            status_code=400,
            detail=e.detail
        )
