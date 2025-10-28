"""
Dependency injection module for the LLM Summarization Microservice.

Provides FastAPI dependency functions for common services and
configuration, following the dependency injection pattern for
better testability and maintainability.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.config import Settings, get_settings
from app.core.constants import ERROR_INVALID_API_KEY, HTTP_UNAUTHORIZED
from app.core.exceptions import AuthenticationError


def get_cached_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses LRU cache to ensure settings are loaded only once per application
    lifecycle, improving performance and ensuring consistency across requests.
    
    Returns:
        Cached Settings instance
        
    Example:
        ```python
        @app.get("/endpoint")
        async def endpoint(settings: Settings = Depends(get_cached_settings)):
            return {"version": settings.api_version}
        ```
    """
    return get_settings()


# Type alias for dependency injection
SettingsDep = Annotated[Settings, Depends(get_cached_settings)]


async def verify_api_key(
    authorization: Annotated[str, Header(description="Authorization header with Bearer token")],
    settings: SettingsDep
) -> str:
    """
    Verify API key from Authorization header.
    
    Validates the API key provided in the Authorization header against
    the configured allowed API keys. Supports Bearer token format.
    
    Args:
        authorization: Authorization header value (format: "Bearer <key>")
        settings: Application settings containing allowed API keys
        
    Returns:
        Validated API key string
        
    Raises:
        HTTPException: If API key is missing, malformed, or invalid
        
    Example:
        ```python
        @app.post("/protected-endpoint")
        async def protected_endpoint(
            api_key: str = Depends(verify_api_key)
        ):
            return {"message": "Access granted"}
        ```
    """
    # Check Authorization header format
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_INVALID_API_KEY,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract API key
    api_key = authorization.replace("Bearer ", "").strip()
    
    # Validate API key is not empty
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_INVALID_API_KEY,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if API key is in allowed list
    if api_key not in settings.api_keys_list:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_INVALID_API_KEY,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return api_key


# Type alias for API key dependency
ApiKeyDep = Annotated[str, Depends(verify_api_key)]


async def get_api_key_hash(api_key: ApiKeyDep) -> int:
    """
    Get anonymized hash of API key for logging.
    
    Creates a consistent hash of the API key for use in logs without
    exposing the actual key value. Uses modulo to create a small
    integer identifier.
    
    Args:
        api_key: Validated API key from verify_api_key dependency
        
    Returns:
        Anonymized hash of the API key (0-9999)
        
    Example:
        ```python
        @app.post("/endpoint")
        async def endpoint(
            api_key_hash: int = Depends(get_api_key_hash)
        ):
            logger.info("request", api_key_hash=api_key_hash)
        ```
    """
    return hash(api_key) % 10000


# Type alias for API key hash dependency
ApiKeyHashDep = Annotated[int, Depends(get_api_key_hash)]


def create_dependency_error_handler():
    """
    Create a dependency error handler for common dependency failures.
    
    Returns a function that can be used to handle dependency injection
    errors consistently across the application.
    
    Returns:
        Error handler function
        
    Example:
        ```python
        error_handler = create_dependency_error_handler()
        app.add_exception_handler(DependencyError, error_handler)
        ```
    """
    def handle_dependency_error(request, exc):
        """Handle dependency injection errors."""
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Dependency injection error / Error de inyección de dependencias"
        )
    
    return handle_dependency_error


# Export commonly used dependencies
__all__ = [
    "get_cached_settings",
    "SettingsDep",
    "verify_api_key", 
    "ApiKeyDep",
    "get_api_key_hash",
    "ApiKeyHashDep",
    "create_dependency_error_handler",
]
