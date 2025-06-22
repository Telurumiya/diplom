from __future__ import annotations

from datetime import datetime
from typing import Annotated, List, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.error import ErrorDetail
from app.utils.enums import DocumentStatus, DocumentTextElementType


class DocumentBase(BaseModel):
    """Base model for document with common attributes.

    Attributes:
        id: The id of the document.
    """

    id: Annotated[
        int,
        Field(
            ...,
            examples=[1],
            description="Document ID",
        ),
    ]


    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        json_schema_extra={
            "example": {
                "id": 1
            }
        },
    )


class DocumentCreate(BaseModel):
    """Model for creating a new document."""

    body: Annotated[
        str,
        Field(
            ...,
            min_length=1,
            max_length=280,
            examples=["Create document"],
            description="Created document).",
        ),
    ]

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        json_schema_extra={"example": {"body": "Hello Twitter clone!"}},
    )


class DocumentUploadResponse(DocumentBase):
    """Response model for document with additional metadata.

    Attributes:
        filename: The filename of the document.
        status: The status of the document.
        uploaded_at: Datetime when the document was uploaded.
    """

    filename: Annotated[
        str,
        Field(
            ...,
            examples=["document.docx"],
            description="Document filename."
        )
    ]
    status: Annotated[
        DocumentStatus,
        Field(
            default=DocumentStatus.PENDING,
            examples=["pending"],
            description="Document status (pending/checked/failed)."
        )
    ]
    uploaded_at: Annotated[
        datetime,
        Field(
            ...,
            examples=["2023-01-01T12:00:00"],
            description="Time of upload document."
        )
    ]

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        json_schema_extra={
            "example": {
                "filename": "example.docx",
                "status": "pending",
                "uploaded_at": "2023-01-01T12:00:00"
            }
        }
    )


class DocumentResponse(DocumentUploadResponse):
    """Response model for document details.

    Attributes:
        filepath: Path to the original document file.
        new_filepath: Path to the checked document file, if available.
        json_filepath: Path to the JSON file with errors, if available.
        error_count: Number of errors found in the document.
        user_id: ID of the user who uploaded the document.
        errors: Grouped errors by type, if available.
    """

    filepath: Annotated[
        str,
        Field(
            ...,
            examples=["uploaded_docs/testuser/2025-05-11/de35745a-ab4f-4aeb-b352-666833aa6395_kurs.docx"],
            description="Path to the original document file",
        ),
    ]
    new_filepath: Annotated[
        Optional[str],
        Field(
            None,
            examples=["uploaded_docs/testuser/2025-05-11/de35745a-ab4f-4aeb-b352-666833aa6395_kurs_NEW.docx"],
            description="Path to the checked document file",
        ),
    ]
    json_filepath: Annotated[
        Optional[str],
        Field(
            None,
            examples=["uploaded_docs/testuser/2025-05-11/de35745a-ab4f-4aeb-b352-666833aa6395_kurs_errors.json"],
            description="Path to the JSON file with errors",
        ),
    ]
    error_count: Annotated[
        Optional[int],
        Field(
            None,
            examples=[3],
            description="Number of errors found in the document",
        ),
    ]
    user_id: Annotated[
        int,
        Field(
            ...,
            examples=[1],
            description="ID of the user who uploaded the document",
        ),
    ]
    errors: Annotated[
        Optional[Dict[str, List[ErrorDetail]]],
        Field(
            None,
            examples=[{
                "structure": [
                    {
                        "type": DocumentTextElementType.STRUCTURE,
                        "message": "Структурный элемент не должен иметь отступ первой строки.",
                        "paragraph_text": "Введение",
                        "index": 41,
                        "element_type": "paragraph"
                    }
                ]
            }],
            description="Grouped errors by type",
        ),
    ]

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "filename": "kurs.docx",
                "status": DocumentStatus.CHECKED,
                "uploaded_at": "2025-05-11T12:00:00",
                "filepath": "uploaded_docs/testuser/2025-05-11/de35745a-ab4f-4aeb-b352-666833aa6395_kurs.docx",
                "new_filepath": "uploaded_docs/testuser/2025-05-11/de35745a-ab4f-4aeb-b352-666833aa6395_kurs_NEW.docx",
                "json_filepath": "uploaded_docs/testuser/2025-05-11/de35745a-ab4f-4aeb-b352-666833aa6395_kurs_errors.json",
                "error_count": 3,
                "user_id": 1,
                "errors": {
                    "structure": [
                        {
                            "type": "structure",
                            "message": "Структурный элемент не должен иметь отступ первой строки.",
                            "paragraph_text": "Введение",
                            "index": 41,
                            "element_type": "paragraph"
                        },
                        {
                            "type": "structure",
                            "message": "После структурного элемента должно быть две пустые строки",
                            "paragraph_text": "Введение",
                            "index": 41,
                            "element_type": "paragraph"
                        },
                        {
                            "type": "structure",
                            "message": "Структурный элемент не должен иметь отступ первой строки.",
                            "paragraph_text": "Заключение",
                            "index": 377,
                            "element_type": "paragraph"
                        }
                    ]
                }
            }
        },
    )