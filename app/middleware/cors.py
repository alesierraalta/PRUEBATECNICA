"""
CORS middleware configuration.

Provides configurable Cross-Origin Resource Sharing (CORS) support
with security best practices and flexible origin management.
"""

from typing import List, Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_cached_settings


def setup_cors(app: FastAPI, settings: Settings = None) -> None:
    """
    Setup CORS middleware with security best practices.
    
    Configures CORS middleware with appropriate settings for
    production and development environments, including security
    headers and origin validation.
    
    Args:
        app: FastAPI application instance
        settings: Application settings (uses cached settings if None)
        
    Example:
        ```python
        app = FastAPI()
        setup_cors(app)
        ```
    """
    if settings is None:
        settings = get_cached_settings()
    
    # Configure CORS origins
    origins = settings.cors_origins
    
    # Add security headers
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "User-Agent",
            "X-Requested-With",
            "X-Request-ID"
        ],
        expose_headers=[
            "X-Request-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset"
        ],
        max_age=3600,  # Cache preflight requests for 1 hour
    )


def create_cors_middleware(origins: List[str]) -> CORSMiddleware:
    """
    Create CORS middleware with custom origins.
    
    Creates a CORS middleware instance with specified origins
    and security best practices.
    
    Args:
        origins: List of allowed origins
        
    Returns:
        CORSMiddleware instance
        
    Example:
        ```python
        cors_middleware = create_cors_middleware(["https://example.com"])
        app.add_middleware(cors_middleware)
        ```
    """
    return CORSMiddleware(
        app=None,  # Will be set when added to app
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "User-Agent",
            "X-Requested-With",
            "X-Request-ID"
        ],
        expose_headers=[
            "X-Request-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset"
        ],
        max_age=3600,
    )


# Export for easy importing
__all__ = [
    "setup_cors",
    "create_cors_middleware",
]
