from __future__ import annotations

from typing import Optional, Union

from pydantic import EmailStr
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.exceptions import AlreadyExistsError, IntegrityError, QueryError
from app.core.logger import app_logger
from app.db.crud.base_crud import BaseCRUD
from app.db.models.user import User


class UserCrud(BaseCRUD[User]):
    """CRUD operations for User model."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize User CRUD operations with a database session.

        Args:
            db: Database session.
        """
        super().__init__(db, User)

    async def get_by_id(
        self, user_id: int, raise_not_found: bool = False
    ) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User ID.
            raise_not_found: Whether to raise exception if user not found.

        Returns:
            User instance or None.
        """
        return await self._get_by_field(
            User.id, user_id, raise_not_found=raise_not_found
        )

    async def get_by_email(
        self, email: Union[EmailStr, str], raise_not_found: bool = False
    ) -> Optional[User]:
        """Get user by email.

        Args:
            email: User email.
            raise_not_found: Whether to raise exception if user not found.

        Returns:
            User instance or None.
        """
        return await self._get_by_field(
            User.email, email, raise_not_found=raise_not_found
        )

    async def get_by_username(
        self, username: str, raise_not_found: bool = False
    ) -> Optional[User]:
        """Get user by username.

        Args:
            username: User username.
            raise_not_found: Whether to raise exception if user not found.

        Returns:
            User instance or None.
        """
        return await self._get_by_field(
            User.username, username, raise_not_found=raise_not_found
        )

    async def get_by_identifier(self, identifier: str) -> Optional[User]:
        """Get user by username or email.

        Args:
            identifier: Username or email.

        Returns:
            User instance or None.
        """
        result = await self.db.execute(
            select(User).filter(
                or_(User.username == identifier, User.email == identifier)
            )
        )
        return result.scalars().first()

    async def create_user(self, user_data: dict) -> User:
        """Create a new user.

        Args:
            user_data: User attributes

        Returns:
            Created user instance

        Raises:
            AlreadyExistsError: If user with email/username exists
            IntegrityError: If database constraints are violated
        """

        try:
            await self.check_user_exists(
                email=user_data.get("email"), username=user_data.get("username")
            )
            user_data["is_verified"] = True
            return await super().create(**user_data)
        except Exception as e:
            app_logger.exception(
                f"Failed to create user {user_data.get('username')}: {e}", exc_info=True
            )
            raise IntegrityError(detail=f"Failed to create user: {str(e)}") from e

    async def check_user_exists(
        self, email: Union[EmailStr, str, None] = None, username: Optional[str] = None
    ) -> Optional[User]:
        """Checks if a user exists in the database.

        Args:
            email: Email address of the user.
            username: Username of the user.

        Raises:
            AlreadyExistsError: If user exists
            QueryError: If query fails
        """
        try:
            if email and await self.get_by_email(email):
                app_logger.error(f"User with {email} already exists")
                raise AlreadyExistsError(model=User, field="email", value=email)

            if username and await self.get_by_username(username):
                app_logger.error(f"User with username {username} already exists.")
                raise AlreadyExistsError(model=User, field="username", value=username)
        except Exception as e:
            app_logger.exception(f"Failed to check user {username}: {e}", exc_info=True)
            raise QueryError(
                query="Check user existence",
                params={"email": email, "username": username},
                detail=str(e),
            ) from e
