from typing import Any, Optional, Type

from pydantic import BaseModel, Field


class DomainException(Exception):
    default_detail: str = "Domain error"

    def __init__(self, detail: Optional[str] = None):
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


# Registration
class SignupException(DomainException):
    """Signup error."""

    default_detail = "Signup error."


class SignupCodeNotFoundError(DomainException):
    """Raised when signup code not found in Redis."""

    default_detail = "Код подтверждения не найден или истёк."


class CorruptedSignupDataError(DomainException):
    """Raised when Redis signup payload is corrupted (invalid JSON)."""

    default_detail = "Redis signup payload is corrupted."


class SignupInvalidConfirmationCodeError(DomainException):
    """Raised when confirmation code is invalid."""

    default_detail = "Invalid confirmation code."


class SignupCodeExistsError(SignupException):
    """Raised when signup code already exists."""

    default_detail = "Signup code already exists."


class SignupDataCorruptedError(SignupException):
    """Raised when signup user data not found in Redis payload."""

    default_detail = "Signup user data corrupted."


class SignupDataNotFoundError(SignupException):
    """Raised when signup data not found in Redis."""

    default_detail = "Signup user data not found."


class SignupEmailNotFoundError(SignupException):
    """Raised when signup email not found in Redis."""

    default_detail = "No email address found in user data."


# Authenticate
class AuthException(DomainException):
    default_detail = "Authentication error."


class PasswordIncorrectError(AuthException):
    """Raised when password is incorrect."""

    default_detail = "Password incorrect."


class UserNotFoundError(AuthException):
    """Raised when user not found in database."""

    default_detail = "User not found."


class MissingTokensError(AuthException):
    """Raised when access or refresh tokens are missing."""

    default_detail = "Missing authentication tokens."


class AccessTokenRevokedError(AuthException):
    """Raised when access token is revoked or expired."""

    default_detail = "Access token revoked or expired."


class RefreshTokenExpiredError(AuthException):
    """Raised when refresh token is expired."""

    default_detail = "Refresh token revoked or expired."


class InvalidAccessTokenError(AuthException):
    """Raised when access token is invalid."""

    default_detail = "Invalid access token."


class InvalidRefreshTokenError(AuthException):
    """Raised when refresh token is invalid."""

    default_detail = "Invalid refresh token."


# Document
class DocumentError(DomainException):
    """Raised when document error."""

    default_detail = "Document error."


class DocumentAccessError(DocumentError):
    """Raised when document access error."""

    default_detail = "Not owner."


# File Storage
class FileStorageError(DomainException):
    """Base class for file storage related exceptions."""

    default_detail = "File storage error."


# CRUD
class RepositoryException(Exception):
    """Base exception for all repository-related errors."""

    default_detail: str = "Repository error"

    def __init__(self, detail: Optional[str] = None) -> None:
        """
        Initialize the exception.

        Args:
            detail: Custom error message. If not provided, default_detail will be used.
        """
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


class NotFoundError(RepositoryException):
    """Raised when a requested resource is not found."""

    default_detail: str = "Object not found"

    def __init__(
        self,
        model: Optional[Type[Any]] = None,
        criteria: Optional[dict[str, Any]] = None,
        detail: Optional[str] = None,
    ) -> None:
        """
        Initialize the not found error.

        Args:
            model: The model class that was not found.
            criteria: The lookup criteria that failed.
            detail: Custom error message.
        """
        if model and not detail:
            self.detail = f"{model.__name__} not found"
            if criteria:
                self.detail += f" with criteria: {criteria}"
        super().__init__(detail)


class AlreadyExistsError(RepositoryException):
    """Raised when trying to create a resource that already exists."""

    default_detail: str = "Resource already exists"

    def __init__(
        self,
        model: Optional[Type[Any]] = None,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        detail: Optional[str] = None,
    ) -> None:
        """
        Initialize the already exists error.

        Args:
            model: The model class that already exists.
            field: The field that caused the conflict.
            value: The value that caused the conflict.
            detail: Custom error message.
        """
        if detail:
            self.detail = detail
        elif model:
            self.detail = f"{model.__name__} already exists"
        elif field:
            self.detail = f"{field.title()} already exists"
        elif model and field and value:
            self.detail = f"{model.__name__} with {field} already exists"
        else:
            self.detail = self.default_detail
        super().__init__(self.detail)


class IntegrityError(RepositoryException):
    """Raised when database integrity constraints are violated."""

    default_detail: str = "Data integrity violation"

    def __init__(
        self, constraint: Optional[str] = None, detail: Optional[str] = None
    ) -> None:
        """
        Initialize the integrity error.

        Args:
            constraint: The database constraint that was violated.
            detail: Custom error message.
        """
        if constraint and not detail:
            self.detail = f"Constraint violation: {constraint}"
        super().__init__(detail)


class OperationForbiddenError(RepositoryException):
    """Raised when an operation is not permitted."""

    default_detail: str = "Operation not permitted"

    def __init__(
        self,
        operation: Optional[str] = None,
        reason: Optional[str] = None,
        detail: Optional[str] = None,
    ) -> None:
        """
        Initialize the operation forbidden error.

        Args:
            operation: The operation that was attempted.
            reason: The reason for the restriction.
            detail: Custom error message.
        """
        if operation and reason and not detail:
            self.detail = f"Cannot {operation}: {reason}"
        super().__init__(detail)


class OptimisticLockError(RepositoryException):
    """Raised when optimistic locking fails."""

    default_detail: str = "Concurrent modification detected"

    def __init__(
        self,
        model: Optional[Type[Any]] = None,
        identifier: Optional[Any] = None,
        detail: Optional[str] = None,
    ) -> None:
        """
        Initialize the optimistic lock error.

        Args:
            model: The model class that had a version conflict.
            identifier: The ID of the conflicting record.
            detail: Custom error message.
        """
        if model and identifier and not detail:
            self.detail = f"Version conflict for {model.__name__} id={identifier}"
        super().__init__(detail)


class QueryError(RepositoryException):
    """Raised when there are problems with query execution."""

    default_detail: str = "Query execution failed"

    def __init__(
        self,
        query: Optional[str] = None,
        params: Optional[dict[str, Any]] = None,
        detail: Optional[str] = None,
    ) -> None:
        """
        Initialize the query error.

        Args:
            query: The problematic query.
            params: The parameters used with the query.
            detail: Custom error message.
        """
        if query and not detail:
            self.detail = f"Failed to execute query: {query}"
            if params:
                self.detail += f" with params: {params}"
        super().__init__(detail)


class CacheError(DomainException):
    """Exception raised for cache-related errors."""

    def __init__(self, detail: str) -> None:
        """Initialize CacheError.

        Args:
            detail: Error message.
        """
        super().__init__(detail=detail)


class ErrorDetail(BaseModel):
    msg: str
    error_code: int
    field: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional field",
    )


class StructureElementError(DomainException):
    """Exception raised for structure element errors."""

    default_detail: str = "Structure element error."