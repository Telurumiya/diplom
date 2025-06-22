from datetime import datetime, timezone

from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column


class CreatedUpdatedMixin:
    """Mixin class that adds created_at and updated_at timestamp fields.

    Attributes:
        created_at: Timestamp when the record was created (timezone-aware).
        updated_at: Timestamp when the record was last updated (timezone-aware),
                    automatically updates on modification.
    """

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(),  # Локальное время сервера
        nullable=False,
        doc="Timestamp when the record was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(),  # Локальное время сервера
        onupdate=lambda: datetime.now(),  # Локальное время при обновлении
        nullable=False,
        doc="Timestamp when the record was last updated",
    )
