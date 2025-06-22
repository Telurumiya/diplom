"""Email sending service via SMTP or MailHog."""

from __future__ import annotations

import smtplib
from datetime import timedelta
from email.mime.text import MIMEText
from typing import Any, Dict

from app.core.config import get_settings
from app.core.logger import app_logger
from app.utils.email_templates import (
    BaseEmailTemplate,
    EmailTemplateFactory,
    EmailTemplateType,
)

settings = get_settings()


class EmailService:
    """Service for sending emails using SMTP."""

    @staticmethod
    def send_email(email_data: Dict[str, str]) -> None:
        """Send email using SMTP service.

        Args:
            email_data: Dictionary containing email details (from, to, subject, text, html).

        Raises:
            smtplib.SMTPException: If email sending fails.
        """
        msg = MIMEText(
            email_data.get("html", email_data["text"]),
            "html" if "html" in email_data else "plain",
        )
        msg["Subject"] = email_data["subject"]
        msg["From"] = email_data["from"]
        msg["To"] = email_data["to"]

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
        except smtplib.SMTPException as exc:
            app_logger.exception(
                "Failed to send email",
                extra={"to": email_data["to"], "host": settings.SMTP_HOST},
            )
            raise exc


class EmailSendService:
    """Facade for generating, sending and tracking emails."""

    def __init__(self, email_service: EmailService | None = None) -> None:
        self.email_service = email_service or EmailService()

    async def send_email_once(
        self, email: str, template_type: str, **kwargs: Any
    ) -> None:
        """Send an email only once per unique context+key.

        Args:
            email: Email address to send to.
            template_type: Type of the template (e.g. 'registration', 'notification').
            **kwargs: Additional arguments used in the template and tracking.
        """
        template = self._resolve_template(template_type)
        email_data: Dict[str, str] = template.get_email_data(email=email, **kwargs)
        self.email_service.send_email(email_data)

    def _resolve_template(self, template_type: str) -> BaseEmailTemplate:
        """Return an instance of an email template class based on the template
         type string.

        Args:
            template_type (str): Type of email template (e.g.
            'registration_confirmation', 'new_chat_message').

        Returns:
            BaseEmailTemplate: An instance of the selected email template class.
        """
        template_enum = EmailTemplateType(template_type)
        return EmailTemplateFactory.create_template(template_enum)
