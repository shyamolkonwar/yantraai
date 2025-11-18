from typing import Any, Dict, Optional
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.requests import Request
import logging

logger = logging.getLogger(__name__)


class YantraAIException(Exception):
    """
    Base exception class for Yantra AI application
    """
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(YantraAIException):
    """
    Exception for validation errors
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class AuthenticationError(YantraAIException):
    """
    Exception for authentication errors
    """
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(YantraAIException):
    """
    Exception for authorization errors
    """
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundError(YantraAIException):
    """
    Exception for resource not found errors
    """
    def __init__(self, message: str, resource_type: str = "Resource"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource_type": resource_type}
        )


class ProcessingError(YantraAIException):
    """
    Exception for document processing errors
    """
    def __init__(self, message: str, job_id: Optional[str] = None):
        details = {}
        if job_id:
            details["job_id"] = job_id
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class StorageError(YantraAIException):
    """
    Exception for storage-related errors
    """
    def __init__(self, message: str, operation: Optional[str] = None):
        details = {}
        if operation:
            details["operation"] = operation
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class OCRError(YantraAIException):
    """
    Exception for OCR processing errors
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"OCR processing failed: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class DatabaseError(YantraAIException):
    """
    Exception for database errors
    """
    def __init__(self, message: str, operation: Optional[str] = None):
        details = {}
        if operation:
            details["operation"] = operation
        super().__init__(
            message=f"Database error: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


async def yantra_exception_handler(request: Request, exc: YantraAIException) -> JSONResponse:
    """
    Global exception handler for YantraAIException
    """
    logger.error(
        f"YantraAIException: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "details": exc.details,
            "path": str(request.url),
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "type": exc.__class__.__name__,
                "details": exc.details
            }
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Global exception handler for HTTPException
    """
    detail = getattr(exc, 'detail', str(exc))
    logger.warning(
        f"HTTPException: {detail}",
        extra={
            "status_code": exc.status_code,
            "path": str(request.url),
            "method": request.method
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": detail,
                "type": "HTTPException"
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unexpected exceptions
    """
    logger.error(
        f"Unexpected exception: {str(exc)}",
        extra={
            "exception_type": exc.__class__.__name__,
            "path": str(request.url),
            "method": request.method
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "An unexpected error occurred. Please try again later.",
                "type": "InternalServerError"
            }
        }
    )
