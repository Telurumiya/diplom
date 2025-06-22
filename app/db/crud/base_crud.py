from typing import Any, Generic, Optional, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, QueryError

T = TypeVar("T")


class BaseCRUD(Generic[T]):
    """Base CRUD operations."""

    def __init__(self, db: AsyncSession, model: type[T]) -> None:
        """Initialize Base CRUD operations with a database session.

        Args:
            db: Async database session.
            model: SQLAlchemy model class.
        """
        self.db = db
        self.model = model
        self.settings = get_settings()

    async def _get_by_field(
        self, field: InstrumentedAttribute, value: Any, raise_not_found: bool = False
    ) -> Optional[T]:
        """Get item by field value.

        Args:
            field: Model field to filter by
            value: Value to filter
            raise_not_found: Whether to raise if item not found

        Returns:
            Found item or None

        Raises:
            NotFoundError: If raise_not_found=True and item not found
            QueryError: If query execution fails
        """
        if not field or value is None:
            raise ValueError("Field and value must be specified")

        try:
            stmt = select(self.model).filter(field == value)
            result = await self.db.execute(stmt)
            item = result.scalars().first()

            if raise_not_found and not item:
                raise NotFoundError(model=self.model, criteria={field.name: value})

            return item
        except Exception as e:
            raise QueryError(
                query=f"Get {self.model.__name__} by {field.name}",
                params={"value": value},
                detail=str(e),
            ) from e

    async def create(self, **kwargs) -> T:
        """Create a new item.

        Args:
            kwargs: Attributes for the new item.

        Returns:
            The created item.
        """
        item = self.model(**kwargs)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def delete(self, item_id: int) -> bool:
        """Delete an item by ID.

        Args:
            item_id: ID of the item to delete.

        Returns:
            True if item was deleted, False if not found.
        """
        item = await self._get_by_field(self.model.id, item_id)
        if not item:
            return False

        await self.db.delete(item)
        await self.db.commit()
        return True
