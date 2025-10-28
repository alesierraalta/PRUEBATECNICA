"""
Global constants for the LLM Summarization Microservice.

Contains application-wide constants used throughout the service
for consistency and maintainability.
"""

from typing import Final

# =============================================================================
# API Constants
# =============================================================================

API_PREFIX: Final[str] = "/v1"
"""API version prefix for all endpoints."""

HEALTH_ENDPOINT: Final[str] = "/healthz"
"""Health check endpoint path."""

SUMMARIZE_ENDPOINT: Final[str] = "/summarize"
"""Text summarization endpoint path."""

# =============================================================================
# HTTP Status Codes
# =============================================================================

HTTP_OK: Final[int] = 200
"""HTTP 200 OK status code."""

HTTP_CREATED: Final[int] = 201
"""HTTP 201 Created status code."""

HTTP_BAD_REQUEST: Final[int] = 400
"""HTTP 400 Bad Request status code."""

HTTP_UNAUTHORIZED: Final[int] = 401
"""HTTP 401 Unauthorized status code."""

HTTP_FORBIDDEN: Final[int] = 403
"""HTTP 403 Forbidden status code."""

HTTP_NOT_FOUND: Final[int] = 404
"""HTTP 404 Not Found status code."""

HTTP_TOO_MANY_REQUESTS: Final[int] = 429
"""HTTP 429 Too Many Requests status code."""

HTTP_PAYLOAD_TOO_LARGE: Final[int] = 413
"""HTTP 413 Payload Too Large status code."""

HTTP_INTERNAL_SERVER_ERROR: Final[int] = 500
"""HTTP 500 Internal Server Error status code."""

HTTP_SERVICE_UNAVAILABLE: Final[int] = 503
"""HTTP 503 Service Unavailable status code."""

# =============================================================================
# Text Processing Constants
# =============================================================================

MIN_TEXT_LENGTH: Final[int] = 10
"""Minimum text length for summarization."""

MAX_TEXT_LENGTH: Final[int] = 50000
"""Maximum text length for summarization."""

MIN_WORDS_COUNT: Final[int] = 5
"""Minimum word count for valid text."""

MIN_SUMMARY_TOKENS: Final[int] = 10
"""Minimum tokens in summary."""

MAX_SUMMARY_TOKENS: Final[int] = 500
"""Maximum tokens in summary."""

# =============================================================================
# LLM Provider Constants
# =============================================================================

GEMINI_PROVIDER: Final[str] = "gemini"
"""Gemini LLM provider identifier."""

GEMINI_MODEL_DEFAULT: Final[str] = "gemini-pro"
"""Default Gemini model."""

FALLBACK_PROVIDER: Final[str] = "textrank-extractive"
"""Fallback extractive provider identifier."""

SIMPLE_FALLBACK_PROVIDER: Final[str] = "simple-extractive-fallback"
"""Simple fallback provider identifier."""

# =============================================================================
# Cache Constants
# =============================================================================

CACHE_NAMESPACE: Final[str] = "summaries"
"""Redis cache namespace."""

CACHE_KEY_PREFIX: Final[str] = "sum"
"""Cache key prefix."""

DEFAULT_CACHE_TTL: Final[int] = 3600
"""Default cache TTL in seconds (1 hour)."""

# =============================================================================
# Rate Limiting Constants
# =============================================================================

RATE_LIMIT_WINDOW: Final[int] = 60
"""Rate limit window in seconds."""

DEFAULT_RATE_LIMIT: Final[int] = 100
"""Default rate limit per window."""

RATE_LIMIT_HEADER: Final[str] = "X-RateLimit-Limit"
"""Rate limit header name."""

RATE_LIMIT_REMAINING_HEADER: Final[str] = "X-RateLimit-Remaining"
"""Rate limit remaining header name."""

RATE_LIMIT_RESET_HEADER: Final[str] = "X-RateLimit-Reset"
"""Rate limit reset header name."""

# =============================================================================
# Evaluation Constants
# =============================================================================

EVALUATION_MODEL_DEFAULT: Final[str] = "all-MiniLM-L6-v2"
"""Default sentence transformer model for evaluation."""

ROUGE_METRICS: Final[list[str]] = ["rouge1", "rouge2", "rougeL"]
"""ROUGE metrics to calculate."""

IDEAL_COMPRESSION_RATIO: Final[float] = 0.20
"""Ideal compression ratio (20% of original)."""

COMPRESSION_TOLERANCE: Final[float] = 0.05
"""Compression ratio tolerance (±5%)."""

# =============================================================================
# Logging Constants
# =============================================================================

LOG_FORMAT: Final[str] = "json"
"""Log format (json for structured logging)."""

LOG_FIELDS: Final[list[str]] = [
    "timestamp",
    "level",
    "logger",
    "message",
    "request_id",
    "api_key_hash",
    "text_length",
    "model",
    "latency_ms",
    "cached",
]
"""Standard log fields for structured logging."""

# =============================================================================
# Error Messages
# =============================================================================

ERROR_INVALID_API_KEY: Final[str] = "Invalid API key / Clave API inválida"
"""Error message for invalid API key."""

ERROR_TEXT_TOO_LONG: Final[str] = "Text exceeds maximum length / Texto excede longitud máxima"
"""Error message for text too long."""

ERROR_TEXT_TOO_SHORT: Final[str] = "Text too short / Texto muy corto"
"""Error message for text too short."""

ERROR_SERVICE_UNAVAILABLE: Final[str] = (
    "Summarization service temporarily unavailable / "
    "Servicio temporalmente no disponible"
)
"""Error message for service unavailable."""

ERROR_INTERNAL_SERVER: Final[str] = (
    "Internal server error / Error interno del servidor"
)
"""Error message for internal server error."""

# =============================================================================
# Success Messages
# =============================================================================

SUCCESS_SUMMARY_GENERATED: Final[str] = "Summary generated successfully"
"""Success message for summary generation."""

SUCCESS_CACHE_HIT: Final[str] = "Result served from cache"
"""Success message for cache hit."""

SUCCESS_FALLBACK_USED: Final[str] = "Fallback summarization used"
"""Success message for fallback usage."""

# =============================================================================
# Timeout Constants
# =============================================================================

DEFAULT_REQUEST_TIMEOUT: Final[int] = 10000
"""Default request timeout in milliseconds."""

DEFAULT_LLM_TIMEOUT: Final[int] = 8000
"""Default LLM timeout in milliseconds."""

MAX_RETRY_ATTEMPTS: Final[int] = 3
"""Maximum retry attempts for LLM calls."""

RETRY_BASE_DELAY: Final[float] = 0.5
"""Base delay for retry exponential backoff in seconds."""

RETRY_MAX_DELAY: Final[float] = 5.0
"""Maximum delay for retry exponential backoff in seconds."""

RETRY_JITTER: Final[float] = 0.3
"""Jitter factor for retry delays."""

# =============================================================================
# Language Constants
# =============================================================================

SUPPORTED_LANGUAGES: Final[list[str]] = [
    "auto",
    "en",
    "es",
    "fr",
    "de",
    "it",
    "pt",
    "ru",
    "zh",
    "ja",
    "ko",
]
"""List of supported languages for summarization."""

DEFAULT_LANGUAGE: Final[str] = "auto"
"""Default language for summarization."""

# =============================================================================
# Tone Constants
# =============================================================================

SUPPORTED_TONES: Final[list[str]] = ["neutral", "concise", "bullet"]
"""List of supported tones for summarization."""

DEFAULT_TONE: Final[str] = "neutral"
"""Default tone for summarization."""

# =============================================================================
# Health Check Constants
# =============================================================================

HEALTH_CHECK_TIMEOUT: Final[int] = 5
"""Health check timeout in seconds."""

HEALTH_CHECK_INTERVAL: Final[int] = 30
"""Health check interval in seconds."""

HEALTH_STATUS_HEALTHY: Final[str] = "healthy"
"""Healthy status for health checks."""

HEALTH_STATUS_DEGRADED: Final[str] = "degraded"
"""Degraded status for health checks."""

HEALTH_STATUS_UNHEALTHY: Final[str] = "unhealthy"
"""Unhealthy status for health checks."""
