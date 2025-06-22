from typing import Optional

from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models.user import User


async def get_user(db: AsyncSession, identifier: int) -> Optional[User]:
    """Fetches a user from the database based on email.

    Args:
        db (AsyncSession): The asynchronous database session.
        identifier (int): Id of the user.

    Returns:
        Optional[User]: User object if found, None otherwise.

    Raises:
        ValueError: If an unsupported field is provided.
    """
    result = await db.execute(select(User).filter(User.id == identifier))
    return result.scalars().first()


async def get_user_by_email(db: AsyncSession, email: EmailStr) -> Optional[User]:
    """Fetches a user from the database based on email.

    Args:
        db (AsyncSession): The asynchronous database session.
        email (EmailStr): Email address of the user.

    Returns:
        Optional[User]: User object if found, None otherwise.

    Raises:
        ValueError: If an unsupported field is provided.
    """
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()


async def create_user(db: AsyncSession, user_data: dict):
    """Creates a new user in the database.

    Args:
        db (AsyncSession): The asynchronous database session.
        user_data (UserCreate): The user data including email, and password.

    Returns:
        User: The newly created user object after committing to the database.
    """
    db_user = User(
        email=user_data.get("email"),
        password=user_data.get("password"),
        is_verified=True,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)


async def update_user_password(db: AsyncSession, user: User, new_password: str) -> None:
    """Update the user's password in the database.

    Args:
        db (AsyncSession): The asynchronous database session.
        user (User): The user object to update.
        new_password (str): The new password to set.

    Example:
        await update_user_password(db, user, "newpassword123")
    """
    user.password = new_password
    await db.commit()
    await db.refresh(user)
