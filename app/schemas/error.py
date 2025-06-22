from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Annotated
from app.utils.enums import DocumentStatus, DocumentElementType, \
    DocumentTextElementType


class ErrorDetail(BaseModel):
    """Model for individual error details in a document.

    Attributes:
        type: The type of error (e.g., structure, list, heading).
        message: Description of the error.
        paragraph_text: Text of the paragraph where the error occurred.
        index: Index of the element in the document.
        element_type: Type of the element (e.g., paragraph, table).
    """

    type: Annotated[
        DocumentTextElementType,
        Field(
            ...,
            examples=["structure"],
            description="The type of error",
        ),
    ]
    message: Annotated[
        str,
        Field(
            ...,
            examples=["Структурный элемент не должен иметь отступ первой строки."],
            description="Description of the error",
        ),
    ]
    paragraph_text: Annotated[
        str,
        Field(
            ...,
            examples=["Введение"],
            description="Text of the paragraph where the error occurred",
        ),
    ]
    index: Annotated[
        int,
        Field(
            ...,
            examples=[41],
            description="Index of the element in the document",
        ),
    ]
    element_type: Annotated[
        str,
        Field(
            ...,
            examples=["paragraph"],
            description="Type of the element",
        ),
    ]

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        json_schema_extra={
            "example": {
                "type": "structure",
                "message": "Структурный элемент не должен иметь отступ первой строки.",
                "paragraph_text": "Введение",
                "index": 41,
                "element_type": "paragraph"
            }
        },
    )
    