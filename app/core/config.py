from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API ---------------------------------------------------------------------
    API_PREFIX: str = Field("/api", alias="API_PREFIX")
    API_VERSION: str = Field("1.0.0", alias="API_VERSION")
    BASE_URL: str = Field("http://localhost:8000", alias="BASE_URL")
    MIDDLEWARE_TYPE: str = Field("HTTP", alias="MIDDLEWARE_TYPE")

    # Auth --------------------------------------------------------------------
    ALGORITHM: str = Field("HS256", alias="ALGORITHM")
    ACCESS_TOKEN_COOKIE: str = Field(
        "access_token_cookie",
        alias="ACCESS_TOKEN_COOKIE_NAME",
        description="Имя HTTP-cookie для хранения access-токена",
    )
    REFRESH_TOKEN_COOKIE: str = Field(
        "refresh_token_cookie",
        alias="REFRESH_TOKEN_COOKIE_NAME",
        description="Имя HTTP-cookie для хранения refresh-токена",
    )
    MIN_TOKEN_LENGTH: int = Field(16, alias="MIN_TOKEN_LENGTH")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(
        1440, alias="REFRESH_TOKEN_EXPIRE_MINUTES"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(30, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    SECRET_KEY: str = Field("somethingsecret", alias="SECRET_KEY")
    RESET_CODE_EXPIRE_MINUTES: int = Field(15, alias="RESET_CODE_EXPIRE_MINUTES")
    SESSION_COOKIE_SECURE: bool = Field(False, alias="SESSION_COOKIE_SECURE")
    SESSION_COOKIE_SAMESITE: str = Field("lax", alias="SESSION_COOKIE_SAMESITE")

    # Database ----------------------------------------------------------------
    DATABASE_URL: str = Field(..., alias="DATABASE_URL")

    # Redis -------------------------------------------------------------------
    REDIS_DB: int = Field(0, alias="REDIS_DB")
    REDIS_HOST: str = Field("redis", alias="REDIS_HOST")
    REDIS_PORT: int = Field(6379, alias="REDIS_PORT")

    # Celery ------------------------------------------------------------------
    CELERY_BROKER_URL: str = Field("redis://redis:6379/0", alias="CELERY_BROKER_URL")
    CELERY_BACKEND_URL: str = Field("redis://redis:6379/0", alias="CELERY_BACKEND_URL")

    ACCEPT_CONTENT: str = Field("json", alias="ACCEPT_CONTENT")
    ENABLE_UTC: bool = Field(True, alias="ENABLE_UTC")
    RESULT_SERIALIZER: str = Field("json", alias="RESULT_SERIALIZER")
    TASK_ACKS_LATE: bool = Field(True, alias="TASK_ACKS_LATE")
    TASK_REJECT_ON_WORKER_LOST: bool = Field(True, alias="TASK_REJECT_ON_WORKER_LOST")
    TASK_RETRY_DELAY: int = Field(60, alias="TASK_RETRY_DELAY")
    TASK_SERIALIZER: str = Field("json", alias="TASK_SERIALIZER")
    TASK_SOFT_TIME_LIMIT: int = Field(300, alias="TASK_SOFT_TIME_LIMIT")
    TASK_TIME_LIMIT: int = Field(3600, alias="TASK_TIME_LIMIT")
    TIMEZONE: str = Field("Europe/Moscow", alias="TIMEZONE")
    WORKER_CONCURRENCY: int = Field(4, alias="WORKER_CONCURRENCY")

    # SMTP / MailHog ----------------------------------------------------------
    MAILHOG_URL: str = Field("http://mailhog:8025", alias="MAILHOG_URL")

    SMTP_HOST: str = Field("localhost", alias="SMTP_HOST")
    SMTP_PORT: int = Field(1025, alias="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(None, alias="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(None, alias="SMTP_PASSWORD")
    SMTP_PROVIDER: Optional[str] = Field("mailhog", alias="SMTP_PROVIDER")
    SMTP_USE_TLS: bool = Field(False, alias="SMTP_USE_TLS")
    SMTP_FROM: str = Field("no-reply@example.com", alias="SMTP_FROM")

    # Logging -----------------------------------------------------------------
    LOG_FILE_RETENTION: int = Field(10, alias="LOG_FILE_RETENTION")
    LOG_FILE_ROTATION: str = Field("10MB", alias="LOG_FILE_ROTATION")
    LOG_FILE: Optional[str] = Field(None, alias="LOG_FILE")
    LOG_LEVEL: str = Field("INFO", alias="LOG_LEVEL")
    LOG_TO_CONSOLE: bool = Field(True, alias="LOG_TO_CONSOLE")

    # Storage -----------------------------------------------------------------
    UPLOAD_DIR: str = Field("uploaded_docs", alias="UPLOAD_DIR")

    # Pagination --------------------------------------------------------------
    DEFAULT_PAGE: int = Field(1, alias="DEFAULT_PAGE")
    DEFAULT_PAGE_LIMIT: int = Field(10, alias="DEFAULT_PAGE_LIMIT")
    MIN_PAGE: int = Field(1, alias="MIN_PAGE")
    MIN_PAGE_LIMIT: int = Field(1, alias="MIN_PAGE_LIMIT")
    MAX_PAGE_LIMIT: int = Field(30, alias="MAX_PAGE_LIMIT")

    def get_accept_content_list(self) -> List[str]:
        """Converts ACCEPT_CONTENT string to a list."""
        return [item.strip() for item in self.ACCEPT_CONTENT.split(",") if item]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
