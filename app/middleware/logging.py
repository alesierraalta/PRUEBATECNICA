"""
Structured logging middleware for request/response tracking.

Provides comprehensive logging of HTTP requests and responses with
structured JSON format for monitoring, debugging, and analytics.
Includes performance metrics and security-aware logging.
"""

import time
import uuid
from typing import Optional

from fastapi import Request, Response
import structlog

from app.core.constants import LOG_FIELDS

logger = structlog.get_logger()


async def logging_middleware(request: Request, call_next):
    """
    Structured logging middleware for HTTP requests.
    
    Logs comprehensive request and response information in structured
    JSON format for monitoring, debugging, and analytics. Includes
    performance metrics and security-aware logging.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/handler in chain
        
    Returns:
        Response from next handler
        
    Example:
        ```python
        app.middleware("http")(logging_middleware)
        ```
    """
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Start timing
    start_time = time.time()
    
    # Extract request information
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent", "")
    
    # Get API key hash if available (for authenticated requests)
    api_key_hash = getattr(request.state, "api_key_hash", None)
    
    # Log request start
    logger.info(
        "request_started",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        query_params=str(request.query_params) if request.query_params else None,
        client_ip=client_ip,
        user_agent=user_agent[:100] if user_agent else None,  # Truncate for privacy
        api_key_hash=api_key_hash,
        content_length=request.headers.get("Content-Length"),
        content_type=request.headers.get("Content-Type")
    )
    
    # Process request
    try:
        response = await call_next(request)
        
        # Calculate processing time
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log successful response
        logger.info(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_ip=client_ip,
            api_key_hash=api_key_hash,
            response_size=response.headers.get("Content-Length"),
            content_type=response.headers.get("Content-Type")
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        # Calculate processing time for failed requests
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log error
        logger.error(
            "request_failed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=500,
            duration_ms=duration_ms,
            client_ip=client_ip,
            api_key_hash=api_key_hash,
            error=str(e),
            error_type=type(e).__name__
        )
        
        # Re-raise exception
        raise


def setup_logging(log_level: str = "INFO") -> None:
    """
    Setup structured logging configuration.
    
    Configures structlog for JSON structured logging with
    appropriate processors and formatters.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Example:
        ```python
        setup_logging("INFO")
        ```
    """
    import logging
    import sys
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )


class SecurityLogger:
    """
    Security-focused logger for authentication and authorization events.
    
    Provides specialized logging for security-related events with
    appropriate anonymization and detail levels.
    """
    
    def __init__(self):
        """Initialize security logger."""
        self.logger = structlog.get_logger("security")
    
    def log_auth_attempt(
        self,
        request_id: str,
        client_ip: Optional[str],
        path: str,
        method: str,
        success: bool,
        api_key_hash: Optional[int] = None,
        reason: Optional[str] = None
    ) -> None:
        """
        Log authentication attempt.
        
        Args:
            request_id: Unique request identifier
            client_ip: Client IP address
            path: Request path
            method: HTTP method
            success: Whether authentication succeeded
            api_key_hash: Anonymized API key hash
            reason: Failure reason if unsuccessful
        """
        if success:
            self.logger.info(
                "auth_success",
                request_id=request_id,
                client_ip=client_ip,
                path=path,
                method=method,
                api_key_hash=api_key_hash
            )
        else:
            self.logger.warning(
                "auth_failure",
                request_id=request_id,
                client_ip=client_ip,
                path=path,
                method=method,
                api_key_hash=api_key_hash,
                reason=reason
            )
    
    def log_rate_limit_hit(
        self,
        request_id: str,
        client_ip: Optional[str],
        path: str,
        method: str,
        limit: int,
        window: int
    ) -> None:
        """
        Log rate limit hit.
        
        Args:
            request_id: Unique request identifier
            client_ip: Client IP address
            path: Request path
            method: HTTP method
            limit: Rate limit value
            window: Time window in seconds
        """
        self.logger.warning(
            "rate_limit_hit",
            request_id=request_id,
            client_ip=client_ip,
            path=path,
            method=method,
            limit=limit,
            window=window
        )
    
    def log_suspicious_activity(
        self,
        request_id: str,
        client_ip: Optional[str],
        path: str,
        method: str,
        activity_type: str,
        details: dict
    ) -> None:
        """
        Log suspicious activity.
        
        Args:
            request_id: Unique request identifier
            client_ip: Client IP address
            path: Request path
            method: HTTP method
            activity_type: Type of suspicious activity
            details: Additional details
        """
        self.logger.warning(
            "suspicious_activity",
            request_id=request_id,
            client_ip=client_ip,
            path=path,
            method=method,
            activity_type=activity_type,
            details=details
        )


# Export for easy importing
__all__ = [
    "logging_middleware",
    "setup_logging",
    "SecurityLogger",
]
