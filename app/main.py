"""
FastAPI application main module.

Creates and configures the FastAPI application with all middleware,
routers, exception handlers, and documentation settings.
"""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.api.v1 import router as v1_router
from app.config import get_settings
from app.core.constants import API_PREFIX
from app.middleware.auth import auth_middleware, create_auth_exception_handler
from app.middleware.logging import logging_middleware, setup_logging
from app.middleware.error_handler import global_error_handler
from app.middleware.cors import setup_cors
from app.middleware.rate_limit import create_rate_limit_middleware
from app.core.exceptions import AuthenticationError, RateLimitExceededError
from slowapi.errors import RateLimitExceeded

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application,
    including service initialization and cleanup.
    
    Yields:
        None: During application runtime
        
    Example:
        ```python
        app = FastAPI(lifespan=lifespan)
        ```
    """
    # Startup
    logger.info("application_startup", message="Starting LLM Summarization API")
    
    try:
        # Initialize services
        settings = get_settings()
        
        # Setup logging
        setup_logging(settings.log_level)
        
        logger.info(
            "application_initialized",
            version=settings.api_version,
            log_level=settings.log_level,
            rate_limit_enabled=settings.enable_rate_limit
        )
        
        yield
        
    except Exception as e:
        logger.error("application_startup_failed", error=str(e))
        raise
    
    # Shutdown
    logger.info("application_shutdown", message="Shutting down LLM Summarization API")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Sets up the complete FastAPI application with all middleware,
    routers, exception handlers, and documentation configuration.
    
    Returns:
        Configured FastAPI application instance
        
    Example:
        ```python
        app = create_app()
        ```
    """
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description="""
        **LLM Summarization API** - High-performance text summarization service.
        
        This API provides intelligent text summarization using advanced AI models
        with comprehensive features including:
        
        * **Multi-language Support**: Automatic language detection and support for multiple languages
        * **Configurable Summarization**: Adjustable length, tone, and style
        * **Intelligent Fallback**: Automatic fallback to extractive summarization
        * **Quality Evaluation**: Optional ROUGE scores and semantic similarity metrics
        * **High Performance**: Redis caching and optimized processing
        * **Rate Limiting**: Per-API-key rate limiting with Redis backend
        * **Comprehensive Monitoring**: Health checks and detailed logging
        
        ## Authentication
        
        All endpoints require API key authentication using the `Authorization` header:
        ```
        Authorization: Bearer your_api_key_here
        ```
        
        ## Rate Limiting
        
        The API implements rate limiting per API key to ensure fair usage:
        - Default limit: 100 requests per minute
        - Headers include current limit status
        - Automatic retry-after information
        
        ## Error Handling
        
        All errors return consistent JSON responses with:
        - Error type and message (bilingual)
        - Timestamp and request ID
        - Appropriate HTTP status codes
        
        ## Health Monitoring
        
        Use the `/v1/healthz` endpoint to monitor service health and
        check connectivity to all dependencies.
        """,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    # Setup CORS
    setup_cors(app, settings)
    
    # Add middleware (order matters)
    app.middleware("http")(logging_middleware)
    app.middleware("http")(auth_middleware)
    
    # Add rate limiting middleware if enabled
    if settings.enable_rate_limit:
        rate_limit_middleware = create_rate_limit_middleware(settings)
        app.middleware("http")(rate_limit_middleware)
    
    # Add exception handlers
    app.add_exception_handler(Exception, global_error_handler)
    app.add_exception_handler(AuthenticationError, create_auth_exception_handler())
    app.add_exception_handler(RateLimitExceeded, global_error_handler)
    
    # Include API routers
    app.include_router(v1_router, prefix=API_PREFIX)
    
    # Add root endpoint
    @app.get(
        "/",
        summary="API Information",
        description="Get basic API information and status",
        tags=["Root"]
    )
    async def root() -> dict:
        """
        Root endpoint with API information.
        
        Returns:
            Basic API information and status
        """
        return {
            "message": "LLM Summarization API",
            "version": settings.api_version,
            "status": "operational",
            "timestamp": time.time(),
            "docs_url": "/docs",
            "health_url": "/v1/healthz"
        }
    
    # Add health check at root level for load balancers
    @app.get(
        "/health",
        summary="Simple Health Check",
        description="Simple health check endpoint for load balancers",
        tags=["Health"]
    )
    async def simple_health() -> dict:
        """
        Simple health check for load balancers.
        
        Returns:
            Simple health status
        """
        return {
            "status": "healthy",
            "timestamp": time.time()
        }
    
    logger.info(
        "fastapi_app_created",
        title=settings.api_title,
        version=settings.api_version,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    return app


# Create the app instance
app = create_app()

# Export for easy importing
__all__ = ["app", "create_app"]
