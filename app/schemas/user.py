from typing import Annotated, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.schemas.document import DocumentResponse


class UserCreate(BaseModel):
    """Model for creating a new user.

    Attributes:
        username (str): Unique username.
        email (EmailStr): User email.
        password (str): User password.
    """

    username: Annotated[
        str,
        Field(
            ...,
            min_length=3,
            max_length=50,
            examples=["testuser"],
            description="Unique username (3-50 characters).)",
        ),
    ]
    email: Annotated[
        EmailStr,
        Field(
            ..., examples=["testuser@example.com"], description="Valid email address."
        ),
    ]
    password: Annotated[
        str,
        Field(
            ...,
            min_length=8,
            max_length=128,
            examples=["SomeThing123@"],
            description="Password (8-128 chars, 1 digit, 1 special char)",
        ),
    ]

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        json_schema_extra={
            "example": {
                "username": "testuser",
                "email": "testuser@example.com",
                "password": "SomeThing123@"
            }
        },
    )

    @field_validator("password")
    def validate_password_complexity(cls, v: str) -> str:
        """Validate password meets complexity requirements.

        Args:
            v: Password string to validate

        Raises:
            ValueError: If password doesn't meet complexity requirements

        Returns:
            Validated password
        """
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least 1 digit")
        if not any(char in "!@#$%^&*()_+" for char in v):
            raise ValueError("Password must contain at least 1 special character")
        return v


class UserLogin(BaseModel):
    """Schema for user authentication (login)."""

    identifier: Annotated[str, Field(..., description="Email or username of the user.")]
    password: Annotated[
        str,
        Field(
            min_length=8,
            max_length=128,
            description="Password (8-128 chars, 1 digit, 1 special char)",
        ),
    ]
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        json_schema_extra={
            "example": {
                "identifier": "testuser or testuser@example.com",
                "password": "SomeThing123@",
            }
        },
    )


class UserResponse(BaseModel):
    """Schema for user response.

    Attributes:
        id (int): Unique user identifier.
        username (str): Unique username.
        email (EmailStr): User email address.
        bio (Optional[str]): User biography.
        is_verified (bool): Email verification status.
        documents_count (int): Verified documents count.
    """

    id: Annotated[
        int,
        Field(
            ...,
            examples=[1],
            description="Unique user identifier.",
        ),
    ]
    username: Annotated[
        str,
        Field(
            ...,
            min_length=3,
            max_length=50,
            examples=["johndoe"],
            description="Unique username (3-50 characters).",
        ),
    ]
    email: Annotated[
        EmailStr,
        Field(
            ...,
            examples=["user@example.com"],
            description="Valid email address.",
        ),
    ]
    bio: Optional[
        Annotated[
            str,
            Field(
                None,
                max_length=500,
                examples=["Software developer from New York"],
                description="Optional user biography (up to 500 characters).",
            ),
        ]
    ] = None
    is_verified: Annotated[
        bool,
        Field(
            False,
            examples=[True],
            description="Email verification status.",
        ),
    ]
    documents_count: Annotated[
        int, Field(0, examples=[42], description="Total documents count")
    ]
    last_documents: List[DocumentResponse] = Field(
        [], description="Preview of user's recent documents"
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "username": "johndoe",
                "email": "john@example.com",
                "bio": "Python developer",
                "is_verified": True,
                "documents": 42,
                "last_documents": [
                    {"id": 1, "body": "First document"},
                    {"id": 2, "body": "Second document"},
                ],
            }
        },
    )


class UserProfileResponse(UserResponse):
    """Schema for user profile response.

    Attributes:
        documents_count (int): Number of checking documents.
    """

    documents_count: Annotated[
        int,
        Field(
            ...,
            examples=[1],
            description="Number of checking documents.",
        ),
    ]


    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        json_schema_extra={
            "example": {
                "documents_count": 1
            }
        },
    )


class RefreshTokenRequest(BaseModel):
    """Pydantic model for refresh token request.

    Attributes:
        refresh_token (str): Valid refresh token for authentication.
    """

    refresh_token: str = Field(
        ...,
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
        description="Valid refresh token",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
        }
    )
