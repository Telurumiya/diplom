from dataclasses import dataclass
from datetime import timedelta
from enum import Enum

from app.core.config import get_settings

settings = get_settings()


@dataclass(frozen=True)
class TokenSettings:
    """Class to store token settings."""

    prefix: str
    ttl: timedelta


class TokenType(Enum):
    """Enum to define different types of tokens."""

    ACCESS = TokenSettings(
        prefix=settings.ACCESS_TOKEN_COOKIE,
        ttl=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    REFRESH = TokenSettings(
        prefix=settings.REFRESH_TOKEN_COOKIE,
        ttl=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
    )
    EMAIL_VERIFY = TokenSettings(prefix="email_verify", ttl=timedelta(minutes=15))

    @property
    def prefix(self) -> str:
        """Get prefix for token type."""
        return self.value.prefix

    @property
    def ttl(self) -> timedelta:
        """Get time-to-live for token type."""
        return self.value.ttl


class DocumentStatus(str, Enum):
    PENDING = "В обработке"
    CHECKED = "Проверен"
    FAILED = "Ошибка"


class DocumentType(str, Enum):
    """Тип документа для скачивания пользователем."""

    ORIGINAL = "Оригинал"
    CHECKED = "Проверенный"


class DocumentElementType(str, Enum):
    """Объект перечисления для указания типа элемента в функцию add_errors."""

    PARAGRAPH = 'paragraph'
    TABLE = 'table'
    PICTURE = 'picture'


class DocumentTextElementType(str, Enum):
    """Тип структурного элемента текста в документе."""

    DEFAULT = 'format'
    HEADING = 'heading'
    LIST = 'list'
    LISTING = 'listing'
    IMAGE = 'image'
    TEXT = 'text'
    TABLE = 'table'
    CODE = 'code'
    STRUCTURE = 'structure'


class EmailTemplateType(Enum):
    """Enum for email template types.

    Attributes:
        REGISTRATION_CONFIRMATION: Registration confirmation email template.
    """

    REGISTRATION_CONFIRMATION = "registration_confirmation"

