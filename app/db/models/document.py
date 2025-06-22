from __future__ import annotations

from sqlalchemy import Integer, String, ForeignKey, Index, TIMESTAMP
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, timezone
from app.db.database import Base
from app.utils.enums import DocumentStatus


document_status_enum = ENUM(
    *[status.value for status in DocumentStatus],
    name="document_status_enum",
    create_constraint=True,
)


class Document(Base):
    """Database model representing documents.

    Attributes:
        id: Unique ID.
        filename: Filename of document.
        filepath: File path to original document.
        new_filepath: File path to checked document.
        json_filepath: File path to JSON document with find errors.
        error_count: Number of errors.
        user_id: User ID who downloaded document.
        uploaded_at: Upload date.
    """
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_document_id", "id"),
        Index("ix_documents_filename_id", "filename"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    filepath: Mapped[str] = mapped_column(String, nullable=False)
    new_filepath: Mapped[str] = mapped_column(String, nullable=True)
    json_filepath: Mapped[str] = mapped_column(String, nullable=True)
    error_count: Mapped[int] = mapped_column(Integer, nullable=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE")
    )
    status: Mapped[DocumentStatus] = mapped_column(
        document_status_enum,
        nullable=False,
        server_default=DocumentStatus.PENDING
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp when the record was created",
    )

    user: Mapped["User"] = relationship("User", back_populates="documents")
