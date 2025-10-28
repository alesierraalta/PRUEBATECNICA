"""
Configuration module for the LLM Summarization Microservice.

Implements 12-factor app configuration using Pydantic Settings.
All configuration is managed through environment variables with
type validation and comprehensive documentation.
"""

from typing import Literal
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings following 12-factor principles.
    
    All settings are configurable via environment variables with automatic
    type validation and comprehensive documentation. Sensitive values like
    API keys are never logged or exposed in error messages.
    
    Attributes:
        api_title: Title of the API service
        api_version: Version of the API
        api_keys_allowed: Comma-separated list of valid API keys
        llm_provider: LLM provider to use (currently only 'gemini')
        gemini_api_key: Google AI API key for Gemini access
        gemini_model: Specific Gemini model to use
        request_timeout_ms: Client request timeout in milliseconds
        llm_timeout_ms: LLM provider timeout in milliseconds
        redis_url: Redis connection URL
        redis_pool_max_connections: Maximum Redis connection pool size
        cache_ttl_seconds: Cache time-to-live in seconds
        enable_rate_limit: Whether to enable rate limiting
        rate_limit_per_minute: Rate limit per IP per minute
        cors_origins: List of allowed CORS origins
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        enable_auto_evaluation: Whether to enable automatic quality evaluation
        evaluation_model: Sentence transformer model for evaluation
        summary_max_tokens: Default maximum tokens in summary
        lang_default: Default language for summarization
        tone_default: Default tone for summarization
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
        validate_assignment=True,  # Validate on assignment
    )
    
    # =============================================================================
    # API Configuration
    # =============================================================================
    
    api_title: str = Field(
        default="LLM Summarization API",
        description="Title of the API service",
        examples=["LLM Summarization API", "Text Summarization Service"]
    )
    
    api_version: str = Field(
        default="1.0.0",
        description="Version of the API",
        pattern=r"^\d+\.\d+\.\d+$",  # Semantic versioning pattern
        examples=["1.0.0", "2.1.3"]
    )
    
    api_keys_allowed: str = Field(
        ...,
        description="Comma-separated list of valid API keys",
        min_length=1,
        examples=["key1,key2,key3", "my_secret_key"]
    )
    
    # =============================================================================
    # LLM Provider Configuration
    # =============================================================================
    
    llm_provider: Literal["gemini"] = Field(
        default="gemini",
        description="LLM provider to use (currently only Gemini supported)",
        examples=["gemini"]
    )
    
    gemini_api_key: str = Field(
        ...,
        description="Google AI API key for Gemini access",
        min_length=20,  # Basic validation for API key length
        examples=["AIzaSyC..."]  # Truncated example
    )
    
    gemini_model: str = Field(
        default="gemini-pro",
        description="Specific Gemini model to use",
        examples=["gemini-pro", "gemini-pro-vision"]
    )
    
    # =============================================================================
    # Timeout Configuration
    # =============================================================================
    
    request_timeout_ms: int = Field(
        default=10000,
        ge=1000,
        le=60000,
        description="Client request timeout in milliseconds",
        examples=[10000, 15000, 30000]
    )
    
    llm_timeout_ms: int = Field(
        default=8000,
        ge=1000,
        le=30000,
        description="LLM provider timeout in milliseconds",
        examples=[5000, 8000, 15000]
    )
    
    # =============================================================================
    # Redis Configuration
    # =============================================================================
    
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL",
        examples=["redis://localhost:6379", "redis://user:pass@host:6379/0"]
    )
    
    redis_pool_max_connections: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Maximum Redis connection pool size",
        examples=[10, 50, 100]
    )
    
    cache_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,  # Max 24 hours
        description="Cache time-to-live in seconds",
        examples=[3600, 7200, 86400]
    )
    
    # =============================================================================
    # Rate Limiting Configuration
    # =============================================================================
    
    enable_rate_limit: bool = Field(
        default=True,
        description="Whether to enable rate limiting",
        examples=[True, False]
    )
    
    rate_limit_per_minute: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Rate limit per IP per minute",
        examples=[50, 100, 500]
    )
    
    # =============================================================================
    # CORS Configuration
    # =============================================================================
    
    cors_origins: list[str] = Field(
        default=["*"],
        description="List of allowed CORS origins",
        examples=[["*"], ["http://localhost:3000"], ["https://example.com"]]
    )
    
    # =============================================================================
    # Logging Configuration
    # =============================================================================
    
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level",
        examples=["DEBUG", "INFO", "WARNING", "ERROR"]
    )
    
    # =============================================================================
    # Evaluation Configuration
    # =============================================================================
    
    enable_auto_evaluation: bool = Field(
        default=True,
        description="Whether to enable automatic quality evaluation",
        examples=[True, False]
    )
    
    evaluation_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence transformer model for semantic similarity evaluation",
        examples=["all-MiniLM-L6-v2", "all-mpnet-base-v2"]
    )
    
    # =============================================================================
    # Summarization Defaults
    # =============================================================================
    
    summary_max_tokens: int = Field(
        default=100,
        ge=10,
        le=500,
        description="Default maximum tokens in summary",
        examples=[50, 100, 200]
    )
    
    lang_default: str = Field(
        default="auto",
        description="Default language for summarization",
        examples=["auto", "en", "es", "fr"]
    )
    
    tone_default: Literal["neutral", "concise", "bullet"] = Field(
        default="neutral",
        description="Default tone for summarization",
        examples=["neutral", "concise", "bullet"]
    )
    
    # =============================================================================
    # Validation Methods
    # =============================================================================
    
    @field_validator("api_keys_allowed")
    @classmethod
    def validate_api_keys(cls, v: str) -> str:
        """
        Validate API keys format.
        
        Args:
            v: Comma-separated API keys string
            
        Returns:
            Validated API keys string
            
        Raises:
            ValueError: If API keys format is invalid
        """
        if not v or not v.strip():
            raise ValueError("API keys cannot be empty")
        
        keys = [key.strip() for key in v.split(",") if key.strip()]
        if not keys:
            raise ValueError("At least one API key must be provided")
        
        # Check for minimum key length (basic security)
        for key in keys:
            if len(key) < 8:
                raise ValueError(f"API key '{key[:4]}...' is too short (minimum 8 characters)")
        
        return v
    
    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v: list[str]) -> list[str]:
        """
        Validate CORS origins format.
        
        Args:
            v: List of CORS origins
            
        Returns:
            Validated CORS origins list
        """
        if not v:
            return ["*"]
        
        # Validate URL format for non-wildcard origins
        for origin in v:
            if origin != "*" and not origin.startswith(("http://", "https://")):
                raise ValueError(f"Invalid CORS origin: {origin}. Must start with http:// or https://")
        
        return v
    
    # =============================================================================
    # Computed Properties
    # =============================================================================
    
    @property
    def api_keys_list(self) -> list[str]:
        """
        Parse comma-separated API keys into list.
        
        Returns:
            List of API keys with whitespace stripped
        """
        return [key.strip() for key in self.api_keys_allowed.split(",") if key.strip()]
    
    @property
    def redis_config(self) -> dict[str, int]:
        """
        Get Redis configuration dictionary.
        
        Returns:
            Dictionary with Redis configuration parameters
        """
        return {
            "max_connections": self.redis_pool_max_connections,
            "ttl": self.cache_ttl_seconds,
        }
    
    @property
    def is_development(self) -> bool:
        """
        Check if running in development mode.
        
        Returns:
            True if log level is DEBUG, False otherwise
        """
        return self.log_level == "DEBUG"
    
    @property
    def is_production(self) -> bool:
        """
        Check if running in production mode.
        
        Returns:
            True if log level is INFO or higher, False otherwise
        """
        return self.log_level in ["INFO", "WARNING", "ERROR"]


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses LRU cache to ensure settings are loaded only once per application
    lifecycle, improving performance and ensuring consistency.
    
    Returns:
        Cached Settings instance
    """
    return Settings()


# Export commonly used settings for convenience
__all__ = ["Settings", "get_settings"]
