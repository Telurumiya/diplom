"""Generation of content for various email templates."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict

from app.core.config import get_settings


settings = get_settings()


class EmailTemplateType(Enum):
    """Enum for email template types."""

    REGISTRATION_CONFIRMATION = "registration_confirmation"
    PASSWORD_RESET = "password_reset"


class BaseEmailTemplate(ABC):
    """Abstract base class for email templates."""

    @abstractmethod
    def get_email_data(self, **kwargs) -> Dict[str, str]:
        """Generate email data for sending.

        Args:
            **kwargs: Template-specific parameters.

        Returns:
            dict: {'from', 'to', 'subject', 'text', 'html'}.
        """
        raise NotImplementedError


class BaseTemplate(BaseEmailTemplate):
    """Base class for HTML/plain email templates with common logic."""

    _subject: str = ""
    _preview_text: str = ""

    def _wrap_html(self, inner_html: str) -> str:
        """Wrap content in basic HTML structure.

        Args:
            inner_html: Inner HTML content.

        Returns:
            str: Full HTML content.
        """
        return "<html><body>" f"{inner_html}" "</body></html>"

    def _build_link(self, endpoint: str, **params: str) -> str:
        """Build URL with query parameters.

        Args:
            endpoint: API endpoint for the link.
            **params: Query parameters as key-value pairs.

        Returns:
            str: Complete URL.
        """
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{settings.BASE_URL}{settings.API_PREFIX}{endpoint}?{query}"

    def get_email_data(self, **kwargs) -> Dict[str, str]:
        """Generate email data using template-specific details.

        Args:
            **kwargs: Must include 'email' and template-specific code (e.g., 'confirmation_code').

        Returns:
            Dict[str, str]: Dictionary with email data ('from', 'to', 'subject', 'text', 'html').

        Raises:
            ValueError: If required parameters are missing.
        """
        email = kwargs.get("email")
        code = kwargs.get(self._code_key)
        if not email or not code:
            raise ValueError(f"Missing required parameters: email and {self._code_key}")

        link = self._build_link(self._endpoint, email=email, code=code)
        text = self._get_text_content(link)
        html = self._wrap_html(self._get_html_content(link, code=code))

        return {
            "from": settings.SMTP_FROM,
            "to": email,
            "subject": self._subject,
            "text": text,
            "html": html,
        }

    @property
    @abstractmethod
    def _code_key(self) -> str:
        """Key for the code parameter in kwargs.

        Returns:
            str: Name of the code parameter (e.g., 'confirmation_code', 'reset_code').
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def _endpoint(self) -> str:
        """API endpoint for the link.

        Returns:
            str: Endpoint path (e.g., '/auth/confirm-signup').
        """
        raise NotImplementedError

    @abstractmethod
    def _get_text_content(self, link: str) -> str:
        """Generate plain text content for the email.

        Args:
            link: URL for the email action.

        Returns:
            str: Plain text content.
        """
        raise NotImplementedError

    @abstractmethod
    def _get_html_content(self, link: str, **kwargs) -> str:
        """Generate HTML content for the email.

        Args:
            link: URL for the email action.

        Returns:
            str: HTML content.
        """
        raise NotImplementedError


class RegistrationConfirmationTemplate(BaseTemplate):
    """Template for registration confirmation email."""

    _subject = "Confirm your registration"
    _code_key = "confirmation_code"
    _endpoint = "/auth/confirm-signup"

    def _get_text_content(self, link: str) -> str:
        """Generate plain text content for registration confirmation.

        Args:
            link: Confirmation URL.

        Returns:
            str: Plain text content.
        """
        return f"Please confirm your registration by clicking this link: {link}"

    def _get_html_content(self, link: str, **kwargs) -> str:
        """Generate HTML content for registration confirmation.

        Args:
            link: Confirmation URL.

        Returns:
            str: HTML content.
        """
        return (
            f"<h2>Welcome!</h2>"
            f"<p>Please confirm your registration:</p>"
            f'<a href="{link}">Confirm registration</a>'
        )


class PasswordResetTemplate(BaseTemplate):
    """Template for password reset email."""

    _subject = "Reset your password"
    _code_key = "reset_code"
    _endpoint = "/auth/reset-password"

    def _get_text_content(self, link: str) -> str:
        """Generate plain text content for password reset.

        Args:
            link: Password reset URL.

        Returns:
            str: Plain text content.
        """
        return f"To reset your password, click this link: {link}"

    def _get_html_content(self, link: str, **kwargs) -> str:
        """Generate HTML content for password reset.

        Args:
            link: Password reset URL.

        Returns:
            str: HTML content.
        """
        return (
            f"<h2>Password reset</h2>"
            f"<p>Get your reset code: {kwargs.get('code')}</p>"
        )


class NewChatMessageTemplate(BaseTemplate):
    """Template for chat message notification."""

    _subject = "You're received a new chat message"
    _code_key = "chat_id"
    _endpoint = "/chats/{chat_id}"

    def _get_text_content(self, link: str) -> str:
        """Plain text for message notification."""
        return "You have a new message in chat.\n" f"Open chat: {link}"

    def _get_html_content(self, link: str, **kwargs) -> str:
        """HTML content for message notification."""
        return (
            "<h3>You have a new chat message!</h3>"
            f"<p><a href='{link}'>Click here to open the chat</a></p>"
        )

    def get_email_data(self, **kwargs) -> Dict[str, str]:
        email = kwargs.get("email")
        chat_id = kwargs.get("chat_id")
        message = kwargs.get("message", "[Message not available]")

        if not email or not chat_id or not message:
            raise ValueError(f"Missing required parameters: email and chat_id")

        link = self._build_link(f"/chats/{chat_id}")
        text = f"You received a new message:\n\n{message}\n\nOpen chat: {link}"
        html = self._wrap_html(
            f"<p><strong>New message:</strong></p><p>{message}</p><p><a href='{link}'>Open Chat</a></p>"
        )

        return {
            "from": settings.SMTP_FROM,
            "to": email,
            "subject": self._subject,
            "text": text,
            "html": html,
        }


class EmailTemplateFactory:
    """Factory for creating email templates."""

    _registry = {
        EmailTemplateType.REGISTRATION_CONFIRMATION: RegistrationConfirmationTemplate,
        EmailTemplateType.PASSWORD_RESET: PasswordResetTemplate
    }

    @classmethod
    def create_template(cls, template_type: EmailTemplateType) -> BaseEmailTemplate:
        """Create email template based on type.

        Args:
            template_type: Type of email template.

        Returns:
            EmailTemplate: Email template instance.

        Raises:
            ValueError: If template type is not supported.
        """
        try:
            return cls._registry[template_type]()
        except KeyError:
            raise ValueError(f"Unsupported template type: {template_type}")


__all__ = ["EmailTemplateType", "EmailTemplateFactory", "BaseEmailTemplate"]
