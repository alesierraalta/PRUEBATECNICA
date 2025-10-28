"""
Custom exceptions for the LLM Summarization Microservice.

Defines application-specific exceptions with bilingual error messages
and structured error details for better error handling and debugging.
"""

from typing import Any, Optional


class SummarizationError(Exception):
    """
    Base exception for all summarization-related errors.
    
    Provides a common base class for all custom exceptions with
    structured error information and bilingual support.
    
    Attributes:
        message: Primary error message
        details: Additional error details dictionary
        error_code: Optional error code for programmatic handling
    """
    
    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        """
        Initialize summarization error.
        
        Args:
            message: Primary error message (bilingual)
            details: Additional error details for debugging
            error_code: Optional error code for programmatic handling
        """
        self.message = message
        self.details = details or {}
        self.error_code = error_code
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ValidationError(SummarizationError):
    """
    Raised when input validation fails.
    
    Used for client-side validation errors that should return
    HTTP 400 Bad Request status.
    """
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        """
        Initialize validation error.
        
        Args:
            message: Validation error message
            field: Field name that failed validation
            value: Value that failed validation
            **kwargs: Additional arguments passed to parent
        """
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)[:100]  # Truncate long values
        
        super().__init__(message, details, **kwargs)


class TextTooLongError(ValidationError):
    """
    Raised when input text exceeds maximum length.
    
    Returns HTTP 413 Payload Too Large status.
    """
    
    def __init__(self, text_length: int, max_length: int = 50000):
        """
        Initialize text too long error.
        
        Args:
            text_length: Actual text length
            max_length: Maximum allowed length
        """
        message = (
            f"Text length ({text_length}) exceeds maximum allowed length ({max_length}) / "
            f"Longitud del texto ({text_length}) excede la longitud máxima permitida ({max_length})"
        )
        super().__init__(
            message,
            field="text",
            value=f"length={text_length}",
            details={
                "text_length": text_length,
                "max_length": max_length,
                "excess_length": text_length - max_length
            }
        )


class TextTooShortError(ValidationError):
    """
    Raised when input text is too short for summarization.
    
    Returns HTTP 400 Bad Request status.
    """
    
    def __init__(self, word_count: int, min_words: int = 5):
        """
        Initialize text too short error.
        
        Args:
            word_count: Actual word count
            min_words: Minimum required words
        """
        message = (
            f"Text too short ({word_count} words), minimum {min_words} words required / "
            f"Texto muy corto ({word_count} palabras), mínimo {min_words} palabras requeridas"
        )
        super().__init__(
            message,
            field="text",
            value=f"words={word_count}",
            details={
                "word_count": word_count,
                "min_words": min_words,
                "missing_words": min_words - word_count
            }
        )


class AuthenticationError(SummarizationError):
    """
    Raised when authentication fails.
    
    Returns HTTP 401 Unauthorized status.
    """
    
    def __init__(self, message: str = "Authentication failed / Autenticación fallida"):
        """
        Initialize authentication error.
        
        Args:
            message: Authentication error message
        """
        super().__init__(
            message,
            error_code="AUTH_FAILED",
            details={"auth_required": True}
        )


class AuthorizationError(SummarizationError):
    """
    Raised when authorization fails.
    
    Returns HTTP 403 Forbidden status.
    """
    
    def __init__(self, message: str = "Access forbidden / Acceso prohibido"):
        """
        Initialize authorization error.
        
        Args:
            message: Authorization error message
        """
        super().__init__(
            message,
            error_code="AUTHZ_FAILED",
            details={"access_denied": True}
        )


class RateLimitExceededError(SummarizationError):
    """
    Raised when rate limit is exceeded.
    
    Returns HTTP 429 Too Many Requests status.
    """
    
    def __init__(
        self,
        limit: int,
        window: int = 60,
        retry_after: Optional[int] = None
    ):
        """
        Initialize rate limit exceeded error.
        
        Args:
            limit: Rate limit per window
            window: Time window in seconds
            retry_after: Seconds to wait before retry
        """
        message = (
            f"Rate limit exceeded ({limit} requests per {window}s) / "
            f"Límite de velocidad excedido ({limit} solicitudes por {window}s)"
        )
        
        details = {
            "rate_limit": limit,
            "window_seconds": window,
            "retry_after": retry_after or window
        }
        
        super().__init__(
            message,
            details=details,
            error_code="RATE_LIMIT_EXCEEDED"
        )


class LLMProviderError(SummarizationError):
    """
    Raised when LLM provider fails.
    
    Returns HTTP 503 Service Unavailable status.
    """
    
    def __init__(
        self,
        message: str,
        provider: str,
        model: Optional[str] = None,
        attempts: Optional[int] = None,
        last_error: Optional[str] = None
    ):
        """
        Initialize LLM provider error.
        
        Args:
            message: Error message
            provider: LLM provider name
            model: Model name that failed
            attempts: Number of attempts made
            last_error: Last error message from provider
        """
        details = {
            "provider": provider,
            "model": model,
            "attempts": attempts,
            "last_error": last_error
        }
        
        super().__init__(
            message,
            details=details,
            error_code="LLM_PROVIDER_ERROR"
        )


class CacheError(SummarizationError):
    """
    Raised when cache operations fail.
    
    Used internally, doesn't typically return HTTP errors
    as cache failures should not break the service.
    """
    
    def __init__(
        self,
        message: str,
        operation: str,
        key: Optional[str] = None
    ):
        """
        Initialize cache error.
        
        Args:
            message: Error message
            operation: Cache operation that failed
            key: Cache key involved
        """
        details = {
            "operation": operation,
            "key": key
        }
        
        super().__init__(
            message,
            details=details,
            error_code="CACHE_ERROR"
        )


class EvaluationError(SummarizationError):
    """
    Raised when evaluation fails.
    
    Used internally, doesn't typically return HTTP errors
    as evaluation failures should not break summarization.
    """
    
    def __init__(
        self,
        message: str,
        metric: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize evaluation error.
        
        Args:
            message: Error message
            metric: Evaluation metric that failed
            model: Evaluation model that failed
        """
        details = {
            "metric": metric,
            "model": model
        }
        
        super().__init__(
            message,
            details=details,
            error_code="EVALUATION_ERROR"
        )


class ConfigurationError(SummarizationError):
    """
    Raised when configuration is invalid.
    
    Used during application startup, typically causes
    application to fail to start.
    """
    
    def __init__(
        self,
        message: str,
        setting: Optional[str] = None,
        value: Optional[Any] = None
    ):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            setting: Configuration setting that failed
            value: Invalid value
        """
        details = {
            "setting": setting,
            "value": str(value) if value is not None else None
        }
        
        super().__init__(
            message,
            details=details,
            error_code="CONFIG_ERROR"
        )


class ServiceUnavailableError(SummarizationError):
    """
    Raised when a required service is unavailable.
    
    Returns HTTP 503 Service Unavailable status.
    """
    
    def __init__(
        self,
        message: str,
        service: str,
        check_type: Optional[str] = None
    ):
        """
        Initialize service unavailable error.
        
        Args:
            message: Error message
            service: Service name that's unavailable
            check_type: Type of health check that failed
        """
        details = {
            "service": service,
            "check_type": check_type
        }
        
        super().__init__(
            message,
            details=details,
            error_code="SERVICE_UNAVAILABLE"
        )


# Export all exceptions for easy importing
__all__ = [
    "SummarizationError",
    "ValidationError",
    "TextTooLongError",
    "TextTooShortError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitExceededError",
    "LLMProviderError",
    "CacheError",
    "EvaluationError",
    "ConfigurationError",
    "ServiceUnavailableError",
]
