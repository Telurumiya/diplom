from __future__ import annotations

from typing import Optional, Sequence, Dict, Any

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from app.core.exceptions import QueryError
from app.core.logger import app_logger
from app.db.crud.base_crud import BaseCRUD
from app.db.models.document import Document
from app.utils.enums import DocumentStatus


class DocumentCrud(BaseCRUD[Document]):
    """CRUD operations for User model."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize Document CRUD operations with a database session.

        Args:
            db: Database session.
        """
        super().__init__(db, Document)

    async def create(self, document_info: Dict[str, str]) -> Document:
        """ Create a new document.

        Args:
            document_info: Information about document.

        Returns:
            Document object.
        """
        return await super().create(**document_info)

    async def get_document(
        self,
        document_id: int
    ) -> Optional[Document]:
        """Get document by ID from database.

        Args:
            document_id: ID of the document.

        Returns:
            Document instance or None.
        """
        return await self._get_by_field(field=Document.id, value=document_id)

    async def update(self, document_id: int, update_data: Dict[str, Any]) -> None:
        """Update a document record in the database.

        Args:
            document_id: ID of the document.
            update_data: Dictionary with data to update (e.g., status, error_count, new_filepath, json_filepath).

        Raises:
            QueryError: If the update fails.
        """
        try:
            stmt = (
                update(Document)
                .where(Document.id == document_id)
                .values(**update_data)
            )
            await self.db.execute(stmt)
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            app_logger.error(
                f"Не удалось обновить документ {document_id}: {e}"
            )
            raise QueryError(
                query="Обновление документа",
                params={"document_id": document_id, "update_data": update_data},
                detail=str(e),
            ) from e

    async def update_status(self, document_id: int, status: DocumentStatus) -> None:
        """Update the status of a document.

        Args:
            document_id: ID of the document.
            status: New status for the document.
        """
        try:
            stmt = (
                update(Document)
                .where(Document.id == document_id)
                .values(status=status)
            )
            await self.db.execute(stmt)
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            app_logger.error(
                f"Failed to update status for document {document_id}: {e}")
            raise QueryError(
                query="Update document status",
                params={"document_id": document_id, "status": status},
                detail=str(e),
            ) from e

    async def update_new_filepath(
        self, document_id: int, path: str
    ) -> None:
        """Update the new filepath of a checked document.

        Args:
            document_id: ID of the document.
            path: File path for checked document version.
        """
        try:
            stmt = (
                update(Document)
                .where(Document.id == document_id)
                .values(new_filepath=path)
            )
            await self.db.execute(stmt)
        except Exception as e:
            app_logger.error(
                f"Failed to update status for document {document_id}: {e}")
            raise QueryError(
                query="Update document status",
                params={"document_id": document_id, "checked_path": path},
                detail=str(e),
            ) from e


    async def get_all_documents(
        self,
        user_id: int,
        page: Optional[int] = None,
        limit: Optional[int] = None
    ) -> Sequence[Document]:
        """Get all documents from database.

        Args:
            user_id: User ID.
            page: Page number for paging.
            limit: Documents limit for page.

        Returns:
            Sequence[Document] instance.
        """
        try:
            stmt = (select(Document)
                    .where(Document.user_id == user_id)
                    .order_by(Document.uploaded_at.desc())
                    )

            if page and limit:
                stmt = stmt.offset((page - 1) * limit).limit(limit)

            result = await self.db.execute(stmt)
            return result.scalars().all()

        except Exception as e:
            app_logger.error(f"Failed to get all posts: {e}")
            raise QueryError(
                query="Get all posts",
                params={"page": page, "limit": limit},
                detail=str(e),
            ) from e


class SyncDocumentCrud:
    """Synchronous CRUD operations for Celery tasks."""
    def __init__(self, db: Session) -> None:
        self.db = db

    def update(self, document_id: int, data: Dict[str, Any]) -> None:
        try:
            stmt = (
                update(Document)
                .where(Document.id == document_id)
                .values(**data)
            )
            self.db.execute(stmt)
            # Commit will happen in get_sync_session_context
        except Exception as e:
            app_logger.error(f"Failed to synchronously update document {document_id}: {e}", exc_info=True)
            raise QueryError(
                query="Synchronous document update",
                params={"document_id": document_id, "data": data},
                detail=str(e),
            ) from e
