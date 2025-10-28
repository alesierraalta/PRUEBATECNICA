"""
Rate limiting utilities using slowapi with Redis backend.

Provides comprehensive rate limiting functionality with per-API-key
tracking, sliding window implementation, and configurable limits.
Includes error handling with bilingual messages and standard headers.
"""

import time
from typing import Optional

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
import structlog

from app.core.constants import (
    RATE_LIMIT_WINDOW,
    DEFAULT_RATE_LIMIT,
    RATE_LIMIT_HEADER,
    RATE_LIMIT_REMAINING_HEADER,
    RATE_LIMIT_RESET_HEADER,
    HTTP_TOO_MANY_REQUESTS,
)
from app.core.exceptions import RateLimitExceededError
from app.config import Settings, get_cached_settings

logger = structlog.get_logger()


def get_api_key_for_rate_limit(request: Request) -> str:
    """
    Get API key hash for rate limiting.
    
    Extracts the API key hash from request state for use as
    the rate limiting key. Falls back to IP address if no
    API key is available.
    
    Args:
        request: FastAPI request object
        
    Returns:
        API key hash or IP address for rate limiting
        
    Example:
        ```python
        limiter = Limiter(key_func=get_api_key_for_rate_limit)
        ```
    """
    # Try to get API key hash from request state
    api_key_hash = getattr(request.state, "api_key_hash", None)
    
    if api_key_hash is not None:
        return f"api_key:{api_key_hash}"
    
    # Fallback to IP address for unauthenticated requests
    client_ip = get_remote_address(request)
    return f"ip:{client_ip}"


def create_rate_limiter(settings: Settings = None) -> Limiter:
    """
    Create rate limiter with Redis backend.
    
    Initializes slowapi Limiter with Redis storage and
    appropriate configuration for distributed rate limiting.
    
    Args:
        settings: Application settings (uses cached settings if None)
        
    Returns:
        Configured Limiter instance
        
    Raises:
        Exception: If Redis connection fails
        
    Example:
        ```python
        limiter = create_rate_limiter()
        ```
    """
    if settings is None:
        settings = get_cached_settings()
    
    try:
        # Create limiter with Redis backend
        limiter = Limiter(
            key_func=get_api_key_for_rate_limit,
            storage_uri=settings.redis_url,
            default_limits=[f"{settings.rate_limit_per_minute}/minute"]
        )
        
        logger.info(
            "rate_limiter_initialized",
            redis_url=settings.redis_url,
            default_limit=f"{settings.rate_limit_per_minute}/minute",
            window_seconds=RATE_LIMIT_WINDOW
        )
        
        return limiter
        
    except Exception as e:
        logger.error(
            "rate_limiter_init_failed",
            error=str(e),
            redis_url=settings.redis_url
        )
        raise Exception(
            f"Failed to initialize rate limiter / Error al inicializar limitador de velocidad: {str(e)}"
        )


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Handle rate limit exceeded errors.
    
    Provides consistent error response for rate limit violations
    with bilingual messages and appropriate headers.
    
    Args:
        request: FastAPI request object
        exc: RateLimitExceeded exception
        
    Returns:
        JSONResponse with rate limit error details
        
    Example:
        ```python
        app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
        ```
    """
    # Get request information
    request_id = getattr(request.state, "request_id", None)
    client_ip = get_remote_address(request)
    api_key_hash = getattr(request.state, "api_key_hash", None)
    
    # Log rate limit hit
    logger.warning(
        "rate_limit_exceeded",
        request_id=request_id,
        client_ip=client_ip,
        api_key_hash=api_key_hash,
        path=request.url.path,
        method=request.method,
        limit=str(exc.detail)
    )
    
    # Calculate retry after time
    retry_after = int(exc.retry_after) if exc.retry_after else RATE_LIMIT_WINDOW
    
    # Create error response
    response = JSONResponse(
        status_code=HTTP_TOO_MANY_REQUESTS,
        content={
            "error": "rate_limit_exceeded",
            "message": (
                f"Rate limit exceeded ({exc.detail}) / "
                f"Límite de velocidad excedido ({exc.detail})"
            ),
            "retry_after": retry_after,
            "timestamp": time.time(),
            "request_id": request_id
        }
    )
    
    # Add rate limit headers
    response.headers["Retry-After"] = str(retry_after)
    response.headers[RATE_LIMIT_HEADER] = str(exc.detail)
    response.headers[RATE_LIMIT_REMAINING_HEADER] = "0"
    response.headers[RATE_LIMIT_RESET_HEADER] = str(int(time.time() + retry_after))
    
    return response


def get_rate_limit_info(request: Request, limiter: Limiter) -> dict:
    """
    Get current rate limit information for a request.
    
    Retrieves current rate limit status including remaining
    requests and reset time for the given request.
    
    Args:
        request: FastAPI request object
        limiter: Limiter instance
        
    Returns:
        Dictionary with rate limit information
        
    Example:
        ```python
        info = get_rate_limit_info(request, limiter)
        print(f"Remaining: {info['remaining']}")
        ```
    """
    try:
        # Get rate limit key
        key = get_api_key_for_rate_limit(request)
        
        # Get current rate limit status
        # Note: This is a simplified implementation
        # In practice, you'd need to query the storage directly
        
        return {
            "limit": DEFAULT_RATE_LIMIT,
            "remaining": "unknown",  # Would need storage query
            "reset": int(time.time() + RATE_LIMIT_WINDOW)
        }
        
    except Exception as e:
        logger.warning(
            "rate_limit_info_failed",
            error=str(e),
            path=request.url.path
        )
        
        return {
            "limit": DEFAULT_RATE_LIMIT,
            "remaining": "unknown",
            "reset": int(time.time() + RATE_LIMIT_WINDOW)
        }


def add_rate_limit_headers(response: JSONResponse, limit_info: dict) -> JSONResponse:
    """
    Add rate limit headers to response.
    
    Adds standard rate limiting headers to the response
    for client information about current limits.
    
    Args:
        response: JSONResponse to modify
        limit_info: Rate limit information dictionary
        
    Returns:
        Modified response with rate limit headers
        
    Example:
        ```python
        response = add_rate_limit_headers(response, limit_info)
        ```
    """
    response.headers[RATE_LIMIT_HEADER] = str(limit_info["limit"])
    response.headers[RATE_LIMIT_REMAINING_HEADER] = str(limit_info["remaining"])
    response.headers[RATE_LIMIT_RESET_HEADER] = str(limit_info["reset"])
    
    return response


class RateLimitManager:
    """
    Rate limit manager for centralized configuration.
    
    Provides centralized management of rate limiting configuration
    and operations with Redis backend integration.
    """
    
    def __init__(self, settings: Settings = None):
        """
        Initialize rate limit manager.
        
        Args:
            settings: Application settings
        """
        if settings is None:
            settings = get_cached_settings()
        
        self.settings = settings
        self.limiter = create_rate_limiter(settings)
        self.enabled = settings.enable_rate_limit
    
    def is_enabled(self) -> bool:
        """
        Check if rate limiting is enabled.
        
        Returns:
            True if rate limiting is enabled
        """
        return self.enabled
    
    def get_limiter(self) -> Limiter:
        """
        Get the configured limiter instance.
        
        Returns:
            Limiter instance
        """
        return self.limiter
    
    def get_limit_string(self) -> str:
        """
        Get rate limit string for configuration.
        
        Returns:
            Rate limit string (e.g., "100/minute")
        """
        return f"{self.settings.rate_limit_per_minute}/minute"
    
    def get_window_seconds(self) -> int:
        """
        Get rate limit window in seconds.
        
        Returns:
            Window size in seconds
        """
        return RATE_LIMIT_WINDOW
    
    def create_limit_decorator(self, limit: str = None):
        """
        Create rate limit decorator.
        
        Args:
            limit: Custom limit string (uses default if None)
            
        Returns:
            Rate limit decorator
        """
        if limit is None:
            limit = self.get_limit_string()
        
        return self.limiter.limit(limit)


# Export for easy importing
__all__ = [
    "get_api_key_for_rate_limit",
    "create_rate_limiter",
    "rate_limit_exceeded_handler",
    "get_rate_limit_info",
    "add_rate_limit_headers",
    "RateLimitManager",
]
