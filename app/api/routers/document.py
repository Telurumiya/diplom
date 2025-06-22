from pathlib import Path
from typing import List, Annotated
from urllib.parse import quote

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.core import get_settings, app_logger
from app.core.exceptions import DomainException
from app.api.dependencies import get_document_service
from app.api.dependencies import verify_user
from app.db.models.user import User
from app.schemas.document import DocumentResponse, DocumentUploadResponse
from app.services.document_service import DocumentService
from app.utils.enums import DocumentType

router = APIRouter(prefix="/documents", tags=["documents"])
settings = get_settings()


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_docx(
    file: UploadFile = File(...),
    user: User = Depends(verify_user),
    document_service: DocumentService = Depends(get_document_service)
) -> DocumentUploadResponse:
    """Upload a file to validate formats.

    Args:
        file: The file to upload.
        user: The authenticated user who uploaded the file.
        document_service: The document service instance to use.

    Returns:
        DocumentUploadResponse: The uploaded file.
    """
    try:
        return await document_service.upload_document(file, user)
    except DomainException as e:
        app_logger.error(f"Error uploading file: {e.detail}")
        raise HTTPException(status_code=400, detail=e.detail)


@router.get("/all", response_model=List[DocumentResponse])
async def get_my_documents(
    page: int = Query(
        settings.DEFAULT_PAGE,
        ge=settings.MIN_PAGE,
        description="The number of posts page.",
    ),
    limit: int = Query(
        settings.DEFAULT_PAGE_LIMIT,
        ge=settings.MIN_PAGE_LIMIT,
        le=settings.MAX_PAGE_LIMIT,
        description="Limit to M posts",
    ),
    user: User = Depends(verify_user),
    document_service: DocumentService = Depends(get_document_service)
) -> List[DocumentResponse]:
    """Get all user documents.

    Args:
        page: Page number.
        limit: Number of documents to return on page.
        user: Authenticated user.
        document_service: The document service instance to use.

    Returns:
        List of documents response schemas.
    """
    try:
        return await document_service.get_all_documents(user, page, limit)
    except DomainException as e:
        app_logger.error(f"Error getting all documents: {e.detail}")
        raise HTTPException(status_code=404, detail=str(e.detail))


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    user: User = Depends(verify_user),
    document_service: DocumentService = Depends(get_document_service)
) -> DocumentResponse:
    """Get document by doc_id.

    Args:
        document_id: Document ID.
        user: Authenticated user.
        document_service: The document service instance to use.

    Returns:
        Document instance or None.
    """
    try:
        return await document_service.get_document(document_id, user)
    except DomainException as e:
        app_logger.error(f"Error getting document {document_id}: {e.detail}")
        raise HTTPException(status_code=404, detail=str(e.detail))


@router.get("/{document_id}/download", response_class=FileResponse)
async def download_document(
    document_id: int,
    doc_type: DocumentType = Query(DocumentType.ORIGINAL),
    user: User = Depends(verify_user),
    document_service: DocumentService = Depends(get_document_service)
):
    """Download document by doc_id.

    Args:
        document_id: Document ID.
        doc_type: Type of document to download.
        user: Authenticated user.
        document_service: The document service instance to use.

    Returns:
        Path for downloaded file.
    """
    try:
        document = await document_service.download_document(document_id, user)

        if doc_type == DocumentType.ORIGINAL:
            path = document.filepath
            file_name = document.filename
        else:
            if not document.new_filepath:
                raise HTTPException(status_code=404, detail="Checked version not ready")
            path = document.new_filepath
            file_name = f"NEW_{document.filename}"

        app_logger.info(f"Downloaded document {document.filename}")
        return FileResponse(
            path=path,
            filename=file_name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                # Для поддержки Unicode в именах файлов
                "Content-Disposition": f"attachment; filename*=UTF-8''{quote(file_name)}"
            },
            content_disposition_type="attachment"  # Принудительное скачивание
        )
    except DomainException as e:
        app_logger.error(f"Error downloading document {document_id}: {e.detail}")
        raise HTTPException(status_code=404, detail=str(e.detail))


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    user: User = Depends(verify_user),
    document_service: DocumentService = Depends(get_document_service)
):
    """Delete document by doc_id.

    Args:
        document_id: Document ID for delete.
        user: Authenticated user.
        document_service: The document service instance to use.

    Returns:

    """
    try:
        await document_service.delete_document(document_id, user)
    except DomainException as e:
        app_logger.error(f"Error deleting document {document_id}: {e.detail}")
        raise HTTPException(status_code=404, detail=str(e.detail))