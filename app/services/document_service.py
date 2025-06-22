import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Any, Coroutine
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_settings, app_logger
from app.core.exceptions import DocumentError, DocumentAccessError
from app.db import User
from app.db.crud.document_crud import DocumentCrud
from app.db.models import Document
from app.schemas.document import DocumentUploadResponse, DocumentResponse
from app.schemas.error import ErrorDetail
from app.services.celery_service import task_process_document_formatting
from app.utils.enums import DocumentStatus

settings = get_settings()


class DocumentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.crud = DocumentCrud(db)

    async def upload_document(
        self, file: UploadFile, user: User
    ) -> DocumentUploadResponse:
        """Upload document to format checking.

        Args:
            file: File to upload.
            user: User who uploaded the document.

        Returns:
            Document response schema.
        """
        content = await file.read()

        date_str = datetime.now().strftime("%Y-%m-%d")
        upload_dir = Path(settings.UPLOAD_DIR) / user.username / date_str
        upload_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid4()}_{file.filename}"
        file_path = upload_dir / filename
        file_path.write_bytes(content)

        document = await self.crud.create({
            "filename": file.filename,
            "filepath": str(file_path),
            "user_id": user.id
        })

        try:
            task_process_document_formatting.delay(document.id, str(file_path))
        except Exception as e:
            app_logger.error(f"Error processing document {document.id}: {e}")
            await self.crud.update_status(document.id, DocumentStatus.FAILED)

        return DocumentUploadResponse(
            id=document.id,
            filename=document.filename,
            status=document.status,
            uploaded_at=document.uploaded_at
        )

    async def get_document(self, document_id: int, user: User) -> DocumentResponse:
        """Get user document by doc_id.

        Args:
            document_id: Document ID.
            user: User instance.

        Returns:
            Document instance.
        """
        document = await self.crud.get_document(document_id)
        if document is None:
            raise DocumentError(detail="Document not found")

        if document.user_id != user.id:
            raise DocumentError(detail="You are not the owner of this document.")

        return await self._enrich_document_response(document)

    async def _enrich_document_response(self, document) -> DocumentResponse:
        """Enrich document response with grouped errors."""
        response = DocumentResponse.model_validate(document)
        if document.json_filepath and Path(document.json_filepath).exists():
            with open(document.json_filepath, 'r', encoding='utf-8') as f:
                errors = json.load(f)
                # Group errors by type
                grouped_errors = {}
                for error in errors:
                    error_type = error['type']
                    if error_type not in grouped_errors:
                        grouped_errors[error_type] = []
                    grouped_errors[error_type].append(ErrorDetail(**error))
                response.errors = grouped_errors
        return response

    async def get_all_documents(
        self,
        user: User,
        page: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[DocumentResponse]:
        """Get all user's documents.

        Args:
            user: User instance.
            page: Page number for paging.
            limit: Documents limit for page.

        Returns:
            List of documents instance.
        """
        documents = await self.crud.get_all_documents(user.id, page, limit)
        return [await self._enrich_document_response(doc) for doc in documents]

    async def download_document(self, document_id: int, user: User) -> Document:
        """Get user document by doc_id.

        Args:
            document_id: Document ID.
            user: Authenticated user instance.

        Returns:
            Path for downloaded file.
        """
        document = await self.crud.get_document(document_id)

        if document is None:
            raise DocumentError(detail="Document not found")

        if document.user_id != user.id:
            raise DocumentAccessError(detail="You are not the owner of this document.")

        return document

    async def delete_document(self, document_id: int, user: User) -> None:
        """Delete user document by doc_id.

        Args:
            document_id: Document ID.
            user: User instance.
        """
        document = await self.crud.get_document(document_id)
        if document is None:
            raise DocumentError(detail="Document not found")
        if document.user_id != user.id:
            raise DocumentError(detail="You are not the owner of this document.")

        path = Path(document.filepath)
        if path.exists():
            path.unlink()

        if document.new_filepath:
            new_path = Path(document.new_filepath)
            if new_path.exists():
                new_path.unlink()

        if document.json_filepath:
            json_path = Path(document.json_filepath)
            if json_path.exists():
                json_path.unlink()

        await self.crud.delete(document_id)
