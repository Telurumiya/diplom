from __future__ import annotations

from typing import List

from pydantic import EmailStr
from sqlalchemy import Boolean, ForeignKey, String, event, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.mixins import CreatedUpdatedMixin


class User(Base, CreatedUpdatedMixin):
    """Database model representing application users.

    Attributes:
        id: Primary key identifier of the user.
        email: Unique email address.
        password: Hashed password for authentication.
        is_verified: Flag indicating if email was verified.
        role_id: Foreign key to user's role (nullable).
        role: Relationship to user's role.
    """

    __tablename__ = "users"
    __allow_unmapped__ = True

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, doc="Primary key identifier of the user"
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, doc="Username login"
    )
    email: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False, doc="Unique email address"
    )
    password: Mapped[str] = mapped_column(
        String(128), nullable=False, doc="Hashed password for authentication"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Flag indicating if email was verified",
    )
    role_id: Mapped[int | None] = mapped_column(
        ForeignKey("roles.id", ondelete="SET NULL"),
        default=1,
        doc="Foreign key to user's role",
    )

    role: Mapped["Role"] = relationship(
        "Role",
        foreign_keys=[role_id],
        lazy="selectin",
        doc="Relationship to user's role",
    )
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="user",
        cascade="all, delete"
    )

    @staticmethod
    def validate_email(mapper, connection, target: User) -> None:
        """Validate email format using Pydantic's EmailStr before insert/update.

        Args:
            mapper: SQLAlchemy mapper instance.
            connection: Active database connection.
            target: User instance being inserted or updated.

        Raises:
            ValueError: If email format is invalid.
        """
        try:
            EmailStr._validate(target.email)
        except ValueError as e:
            raise ValueError(f"Invalid email format: {target.email}") from e


event.listen(User, "before_insert", User.validate_email)
event.listen(User, "before_update", User.validate_email)
