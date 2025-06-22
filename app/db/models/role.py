from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.db.mixins import CreatedUpdatedMixin


class Role(Base, CreatedUpdatedMixin):
    """Database model representing user roles and permissions.

    Attributes:
        id: Primary key identifier of the role.
        name: Unique name of the role.
    """

    __tablename__ = "roles"
    __allow_unmapped__ = True

    id: Mapped[int] = mapped_column(
        primary_key=True, doc="Primary key identifier of the role"
    )
    name: Mapped[str] = mapped_column(
        String, nullable=False, unique=True, doc="Unique name of the role"
    )
