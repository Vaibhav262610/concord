"""
Custom exceptions and error handlers for CONCORD API
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConcordException(Exception):
    """Base exception for CONCORD-specific errors"""
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(ConcordException):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__("AUTHENTICATION_FAILED", message, status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(ConcordException):
    """Authorization/permission denied"""
    def __init__(self, message: str = "Permission denied"):
        super().__init__("PERMISSION_DENIED", message, status.HTTP_403_FORBIDDEN)


class ValidationError(ConcordException):
    """Request validation error"""
    def __init__(self, code: str, message: str):
        super().__init__(code, message, status.HTTP_400_BAD_REQUEST)


class NotFoundError(ConcordException):
    """Resource not found"""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            "NOT_FOUND",
            f"{resource} '{identifier}' not found",
            status.HTTP_404_NOT_FOUND
        )


class DuplicateError(ConcordException):
    """Duplicate resource"""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            "DUPLICATE_RESOURCE",
            f"{resource} '{identifier}' already exists",
            status.HTTP_409_CONFLICT
        )


class PolicyViolationError(ConcordException):
    """Policy violation"""
    def __init__(self, message: str):
        super().__init__("POLICY_VIOLATION", message, status.HTTP_403_FORBIDDEN)


async def concord_exception_handler(request: Request, exc: ConcordException):
    """Handler for CONCORD-specific exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "path": str(request.url.path)
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler for Pydantic validation errors"""
    errors = exc.errors()
    
    # Format validation errors
    formatted_errors = []
    for error in errors:
        field = ".".join(str(loc) for loc in error["loc"])
        formatted_errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"Validation error on {request.url.path}: {formatted_errors}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": formatted_errors,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "path": str(request.url.path)
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handler for unexpected exceptions"""
    logger.error(
        f"Unexpected error on {request.url.path}: {str(exc)}",
        exc_info=True
    )
    
    # Don't expose internal errors in production
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "path": str(request.url.path)
            }
        }
    )
