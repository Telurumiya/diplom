"""Generation of content for various email templates."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict

from app.core.config import get_settings
from app.utils.enums import EmailTemplateType

settings = get_settings()


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
        html = self._wrap_html(self._get_html_content(link))

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
    def _get_html_content(self, link: str) -> str:
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

    def _get_html_content(self, link: str) -> str:
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


class EmailTemplateFactory:
    """Factory for creating email templates."""

    @staticmethod
    def create_template(template_type: EmailTemplateType) -> BaseEmailTemplate:
        """Create an email template instance.

        Args:
            template_type: Type of email template.

        Returns:
            An instance of the selected email template class.
        """
        templates = {
            EmailTemplateType.REGISTRATION_CONFIRMATION: RegistrationConfirmationTemplate
        }
        return templates[template_type]()


__all__ = ["EmailTemplateType", "EmailTemplateFactory", "BaseEmailTemplate"]
