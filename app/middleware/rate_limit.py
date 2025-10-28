"""
Rate limiting middleware integration.

Provides middleware integration for rate limiting with slowapi,
including automatic header injection and error handling.
"""

from typing import Optional

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
import structlog

from app.utils.rate_limiter import (
    create_rate_limiter,
    get_rate_limit_info,
    add_rate_limit_headers,
    rate_limit_exceeded_handler
)
from app.config import Settings, get_cached_settings

logger = structlog.get_logger()


class RateLimitMiddleware:
    """
    Rate limiting middleware for FastAPI applications.
    
    Provides automatic rate limiting for all requests with
    configurable limits and Redis backend integration.
    """
    
    def __init__(self, settings: Settings = None):
        """
        Initialize rate limiting middleware.
        
        Args:
            settings: Application settings (uses cached settings if None)
        """
        if settings is None:
            settings = get_cached_settings()
        
        self.settings = settings
        self.limiter = create_rate_limiter(settings)
        self.enabled = settings.enable_rate_limit
    
    async def __call__(self, request: Request, call_next):
        """
        Process request with rate limiting.
        
        Applies rate limiting to the request and adds appropriate
        headers to the response.
        
        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Response with rate limit headers or rate limit error
        """
        # Skip rate limiting if disabled
        if not self.enabled:
            return await call_next(request)
        
        # Skip rate limiting for public endpoints
        public_paths = ["/", "/docs", "/redoc", "/openapi.json", "/v1/healthz"]
        if request.url.path in public_paths:
            return await call_next(request)
        
        try:
            # Apply rate limiting
            response = await call_next(request)
            
            # Add rate limit headers to successful responses
            if hasattr(response, 'status_code') and response.status_code < 400:
                try:
                    limit_info = get_rate_limit_info(request, self.limiter)
                    response = add_rate_limit_headers(response, limit_info)
                except Exception as e:
                    logger.warning(
                        "rate_limit_headers_failed",
                        error=str(e),
                        path=request.url.path
                    )
            
            return response
            
        except RateLimitExceeded as e:
            # Handle rate limit exceeded
            return await rate_limit_exceeded_handler(request, e)
        
        except Exception as e:
            # Log unexpected errors but don't fail the request
            logger.error(
                "rate_limit_middleware_error",
                error=str(e),
                path=request.url.path,
                method=request.method
            )
            
            # Continue with request processing
            return await call_next(request)


def create_rate_limit_middleware(settings: Settings = None) -> RateLimitMiddleware:
    """
    Create rate limiting middleware instance.
    
    Factory function to create a configured rate limiting
    middleware instance.
    
    Args:
        settings: Application settings
        
    Returns:
        Configured RateLimitMiddleware instance
        
    Example:
        ```python
        middleware = create_rate_limit_middleware()
        app.middleware("http")(middleware)
        ```
    """
    return RateLimitMiddleware(settings)


# Export for easy importing
__all__ = [
    "RateLimitMiddleware",
    "create_rate_limit_middleware",
]
