"""
Authentication middleware for API key validation.

Provides Bearer token authentication with comprehensive security features,
bilingual error messages, and detailed logging for monitoring and debugging.
"""

import time
from typing import Optional

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import structlog

from app.core.constants import (
    ERROR_INVALID_API_KEY,
    HTTP_UNAUTHORIZED,
    HTTP_FORBIDDEN,
)
from app.core.dependencies import get_cached_settings
from app.config import Settings

logger = structlog.get_logger()


class AuthenticationError(HTTPException):
    """
    Custom authentication error with bilingual messages.
    
    Provides consistent error responses for authentication failures
    with appropriate HTTP status codes and bilingual error messages.
    """
    
    def __init__(
        self,
        detail: str,
        status_code: int = HTTP_UNAUTHORIZED,
        headers: Optional[dict] = None
    ):
        """
        Initialize authentication error.
        
        Args:
            detail: Error message (bilingual)
            status_code: HTTP status code
            headers: Additional headers
        """
        if headers is None:
            headers = {"WWW-Authenticate": "Bearer"}
        
        super().__init__(status_code=status_code, detail=detail, headers=headers)


async def authenticate_api_key(request: Request) -> str:
    """
    Authenticate API key from Authorization header.
    
    Validates Bearer token authentication against configured API keys
    with comprehensive error handling and security logging.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Validated API key
        
    Raises:
        AuthenticationError: If authentication fails
        
    Example:
        ```python
        @app.get("/protected")
        async def protected_endpoint(api_key: str = Depends(authenticate_api_key)):
            return {"message": "Access granted"}
        ```
    """
    # Get settings
    settings = get_cached_settings()
    
    # Extract Authorization header
    authorization = request.headers.get("Authorization")
    
    if not authorization:
        logger.warning(
            "authentication_failed",
            reason="missing_authorization_header",
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else None
        )
        raise AuthenticationError(
            "Authorization header required / Encabezado de autorización requerido"
        )
    
    # Validate Bearer format
    if not authorization.startswith("Bearer "):
        logger.warning(
            "authentication_failed",
            reason="invalid_authorization_format",
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else None
        )
        raise AuthenticationError(
            "Invalid authorization format. Use 'Bearer <token>' / "
            "Formato de autorización inválido. Use 'Bearer <token>'"
        )
    
    # Extract API key
    api_key = authorization.replace("Bearer ", "").strip()
    
    if not api_key:
        logger.warning(
            "authentication_failed",
            reason="empty_api_key",
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else None
        )
        raise AuthenticationError(
            "API key cannot be empty / Clave API no puede estar vacía"
        )
    
    # Validate API key
    if api_key not in settings.api_keys_list:
        # Log failed attempt with anonymized key for security
        api_key_hash = hash(api_key) % 10000
        logger.warning(
            "authentication_failed",
            reason="invalid_api_key",
            api_key_hash=api_key_hash,
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else None
        )
        raise AuthenticationError(
            ERROR_INVALID_API_KEY
        )
    
    # Log successful authentication
    api_key_hash = hash(api_key) % 10000
    logger.info(
        "authentication_successful",
        api_key_hash=api_key_hash,
        path=request.url.path,
        method=request.method,
        client_ip=request.client.host if request.client else None
    )
    
    return api_key


async def auth_middleware(request: Request, call_next):
    """
    Authentication middleware for API key validation.
    
    Intercepts requests and validates API key authentication
    before allowing access to protected endpoints.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/handler in chain
        
    Returns:
        Response from next handler or authentication error
        
    Example:
        ```python
        app.middleware("http")(auth_middleware)
        ```
    """
    # Skip authentication for public endpoints
    public_paths = ["/", "/docs", "/redoc", "/openapi.json", "/v1/healthz"]
    
    if request.url.path in public_paths:
        return await call_next(request)
    
    try:
        # Authenticate API key
        api_key = await authenticate_api_key(request)
        
        # Add API key to request state for use in handlers
        request.state.api_key = api_key
        request.state.api_key_hash = hash(api_key) % 10000
        
        # Continue to next handler
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response
        
    except AuthenticationError as e:
        # Return authentication error response
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": "authentication_failed",
                "message": e.detail,
                "timestamp": time.time()
            },
            headers=e.headers
        )
    
    except Exception as e:
        # Log unexpected errors
        logger.error(
            "authentication_error",
            error=str(e),
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else None
        )
        
        # Return generic error
        return JSONResponse(
            status_code=HTTP_UNAUTHORIZED,
            content={
                "error": "authentication_error",
                "message": "Authentication service error / Error del servicio de autenticación",
                "timestamp": time.time()
            }
        )


def create_auth_exception_handler():
    """
    Create authentication exception handler.
    
    Returns a handler function for AuthenticationError exceptions
    that provides consistent error responses.
    
    Returns:
        Exception handler function
        
    Example:
        ```python
        app.add_exception_handler(AuthenticationError, create_auth_exception_handler())
        ```
    """
    async def auth_exception_handler(request: Request, exc: AuthenticationError):
        """Handle authentication exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "authentication_failed",
                "message": exc.detail,
                "timestamp": time.time()
            },
            headers=exc.headers
        )
    
    return auth_exception_handler


# Export for easy importing
__all__ = [
    "AuthenticationError",
    "authenticate_api_key",
    "auth_middleware",
    "create_auth_exception_handler",
]
