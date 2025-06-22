from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator

from sqlalchemy import select, create_engine
from sqlalchemy.ext.asyncio import AsyncAttrs, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings


settings = get_settings()


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


async_engine = create_async_engine(settings.DATABASE_URL)
sync_engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""), future=True)

SyncSession = sessionmaker(
    bind=sync_engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def get_async_session_context() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session for direct use in async context.

    Yields:
        AsyncSession: A configured async SQLAlchemy session.

    Raises:
        Exception: If an error occurs during session operations.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@contextmanager
def get_sync_session_context():
    """Sync context for  Celery."""
    session = SyncSession()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()



async def init_db():
    """Initialize db schema."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Вставка роли "студент", если нет
    from app.db.models.role import Role
    async with async_session() as session:
        result = await session.execute(select(Role).where(Role.name == "студент"))
        exists = result.scalar_one_or_none()
        if not exists:
            session.add(Role(name="студент"))
            await session.commit()

__all__ = ["Base", "get_async_session_context", "init_db"]
