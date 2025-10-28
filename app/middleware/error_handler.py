"""
Global error handling middleware.

Provides comprehensive error handling for all application errors
with consistent response format, bilingual error messages, and
detailed logging for debugging and monitoring.
"""

import time
from typing import Union

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog

from app.core.constants import (
    HTTP_BAD_REQUEST,
    HTTP_INTERNAL_SERVER_ERROR,
    HTTP_SERVICE_UNAVAILABLE,
    ERROR_INTERNAL_SERVER,
    ERROR_SERVICE_UNAVAILABLE,
)
from app.core.exceptions import (
    SummarizationError,
    ValidationError,
    LLMProviderError,
    CacheError,
    EvaluationError,
    ServiceUnavailableError,
)

logger = structlog.get_logger()


async def global_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global error handler for all application exceptions.
    
    Provides consistent error response format with appropriate
    HTTP status codes, bilingual error messages, and detailed
    logging for debugging and monitoring.
    
    Args:
        request: FastAPI request object
        exc: Exception that occurred
        
    Returns:
        JSONResponse with error details
        
    Example:
        ```python
        app.add_exception_handler(Exception, global_error_handler)
        ```
    """
    # Get request ID if available
    request_id = getattr(request.state, "request_id", None)
    
    # Get client information
    client_ip = request.client.host if request.client else None
    
    # Get API key hash if available
    api_key_hash = getattr(request.state, "api_key_hash", None)
    
    # Handle different exception types
    if isinstance(exc, HTTPException):
        # FastAPI HTTP exceptions
        status_code = exc.status_code
        error_message = exc.detail
        
        logger.warning(
            "http_exception",
            request_id=request_id,
            status_code=status_code,
            error_message=error_message,
            path=request.url.path,
            method=request.method,
            client_ip=client_ip,
            api_key_hash=api_key_hash
        )
        
        return JSONResponse(
            status_code=status_code,
            content={
                "error": "http_error",
                "message": error_message,
                "status_code": status_code,
                "timestamp": time.time(),
                "request_id": request_id
            }
        )
    
    elif isinstance(exc, RequestValidationError):
        # Pydantic validation errors
        errors = exc.errors()
        
        logger.warning(
            "validation_error",
            request_id=request_id,
            errors=errors,
            path=request.url.path,
            method=request.method,
            client_ip=client_ip,
            api_key_hash=api_key_hash
        )
        
        return JSONResponse(
            status_code=HTTP_BAD_REQUEST,
            content={
                "error": "validation_error",
                "message": "Request validation failed / Validación de solicitud falló",
                "details": errors,
                "timestamp": time.time(),
                "request_id": request_id
            }
        )
    
    elif isinstance(exc, SummarizationError):
        # Custom summarization errors
        status_code = HTTP_SERVICE_UNAVAILABLE
        error_message = exc.message
        
        logger.error(
            "summarization_error",
            request_id=request_id,
            error_code=exc.error_code,
            error_message=error_message,
            error_details=exc.details,
            path=request.url.path,
            method=request.method,
            client_ip=client_ip,
            api_key_hash=api_key_hash
        )
        
        return JSONResponse(
            status_code=status_code,
            content={
                "error": "summarization_error",
                "message": error_message,
                "error_code": exc.error_code,
                "details": exc.details,
                "timestamp": time.time(),
                "request_id": request_id
            }
        )
    
    elif isinstance(exc, ValidationError):
        # Custom validation errors
        status_code = HTTP_BAD_REQUEST
        error_message = exc.message
        
        logger.warning(
            "validation_error",
            request_id=request_id,
            error_message=error_message,
            error_details=exc.details,
            path=request.url.path,
            method=request.method,
            client_ip=client_ip,
            api_key_hash=api_key_hash
        )
        
        return JSONResponse(
            status_code=status_code,
            content={
                "error": "validation_error",
                "message": error_message,
                "details": exc.details,
                "timestamp": time.time(),
                "request_id": request_id
            }
        )
    
    elif isinstance(exc, LLMProviderError):
        # LLM provider errors
        status_code = HTTP_SERVICE_UNAVAILABLE
        error_message = exc.message
        
        logger.error(
            "llm_provider_error",
            request_id=request_id,
            error_message=error_message,
            error_details=exc.details,
            path=request.url.path,
            method=request.method,
            client_ip=client_ip,
            api_key_hash=api_key_hash
        )
        
        return JSONResponse(
            status_code=status_code,
            content={
                "error": "llm_provider_error",
                "message": error_message,
                "details": exc.details,
                "timestamp": time.time(),
                "request_id": request_id
            }
        )
    
    elif isinstance(exc, (CacheError, EvaluationError)):
        # Non-critical errors (cache, evaluation)
        status_code = HTTP_INTERNAL_SERVER_ERROR
        error_message = exc.message
        
        logger.warning(
            "non_critical_error",
            request_id=request_id,
            error_type=type(exc).__name__,
            error_message=error_message,
            error_details=exc.details,
            path=request.url.path,
            method=request.method,
            client_ip=client_ip,
            api_key_hash=api_key_hash
        )
        
        return JSONResponse(
            status_code=status_code,
            content={
                "error": "service_error",
                "message": ERROR_INTERNAL_SERVER,
                "timestamp": time.time(),
                "request_id": request_id
            }
        )
    
    elif isinstance(exc, ServiceUnavailableError):
        # Service unavailable errors
        status_code = HTTP_SERVICE_UNAVAILABLE
        error_message = exc.message
        
        logger.error(
            "service_unavailable",
            request_id=request_id,
            error_message=error_message,
            error_details=exc.details,
            path=request.url.path,
            method=request.method,
            client_ip=client_ip,
            api_key_hash=api_key_hash
        )
        
        return JSONResponse(
            status_code=status_code,
            content={
                "error": "service_unavailable",
                "message": error_message,
                "details": exc.details,
                "timestamp": time.time(),
                "request_id": request_id
            }
        )
    
    else:
        # Unexpected errors
        logger.exception(
            "unexpected_error",
            request_id=request_id,
            error_type=type(exc).__name__,
            error_message=str(exc),
            path=request.url.path,
            method=request.method,
            client_ip=client_ip,
            api_key_hash=api_key_hash
        )
        
        return JSONResponse(
            status_code=HTTP_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_server_error",
                "message": ERROR_INTERNAL_SERVER,
                "timestamp": time.time(),
                "request_id": request_id
            }
        )


def create_error_response(
    error_type: str,
    message: str,
    status_code: int = HTTP_INTERNAL_SERVER_ERROR,
    details: dict = None,
    request_id: str = None
) -> JSONResponse:
    """
    Create standardized error response.
    
    Provides a consistent format for error responses across
    the application with appropriate status codes and details.
    
    Args:
        error_type: Type of error
        message: Error message
        status_code: HTTP status code
        details: Additional error details
        request_id: Request identifier
        
    Returns:
        JSONResponse with error information
        
    Example:
        ```python
        response = create_error_response(
            "validation_error",
            "Invalid input",
            400,
            {"field": "text"}
        )
        ```
    """
    content = {
        "error": error_type,
        "message": message,
        "timestamp": time.time()
    }
    
    if details:
        content["details"] = details
    
    if request_id:
        content["request_id"] = request_id
    
    return JSONResponse(
        status_code=status_code,
        content=content
    )


# Export for easy importing
__all__ = [
    "global_error_handler",
    "create_error_response",
]
