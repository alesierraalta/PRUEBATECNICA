"""
Health check API router.

Provides comprehensive health monitoring for all service components
including LLM providers, cache services, and evaluation services.
"""

import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
import structlog

from app.api.schemas.health import HealthResponse, ServiceStatus
from app.core.dependencies import SettingsDep
from app.core.constants import (
    HEALTH_STATUS_HEALTHY,
    HEALTH_STATUS_DEGRADED,
    HEALTH_STATUS_UNHEALTHY,
)
from app.providers.llm.gemini import GeminiProvider
from app.services.cache import CacheService
from app.services.evaluation import SummaryEvaluator
from app.config import Settings

logger = structlog.get_logger()

router = APIRouter()


async def check_llm_provider(settings: SettingsDep) -> ServiceStatus:
    """
    Check LLM provider health.
    
    Tests connectivity and basic functionality of the LLM provider
    to ensure it's available for summarization requests.
    
    Args:
        settings: Application settings
        
    Returns:
        ServiceStatus with LLM provider health information
    """
    start_time = time.time()
    
    try:
        # Create provider instance
        provider = GeminiProvider(
            api_key=settings.gemini_api_key,
            model_name=settings.gemini_model,
            timeout_seconds=5,  # Short timeout for health check
            max_attempts=1
        )
        
        # Test with a simple request
        test_text = "This is a test for health check."
        result = await provider.summarize(
            text=test_text,
            max_tokens=10,
            lang="en",
            tone="neutral"
        )
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return ServiceStatus(
            status=HEALTH_STATUS_HEALTHY,
            response_time_ms=response_time_ms,
            details={
                "model": settings.gemini_model,
                "provider": "gemini",
                "test_summary_length": len(result["summary"])
            }
        )
        
    except Exception as e:
        logger.warning(
            "llm_provider_health_check_failed",
            error=str(e),
            model=settings.gemini_model
        )
        
        return ServiceStatus(
            status=HEALTH_STATUS_UNHEALTHY,
            response_time_ms=int((time.time() - start_time) * 1000),
            error=str(e),
            details={
                "model": settings.gemini_model,
                "provider": "gemini"
            }
        )


async def check_cache_service(settings: SettingsDep) -> ServiceStatus:
    """
    Check cache service health.
    
    Tests connectivity and basic operations of the cache service
    to ensure it's available for caching operations.
    
    Args:
        settings: Application settings
        
    Returns:
        ServiceStatus with cache service health information
    """
    start_time = time.time()
    
    try:
        # Create cache service instance
        cache_service = CacheService(
            redis_url=settings.redis_url,
            ttl_seconds=60,
            namespace="health_check"
        )
        
        # Test basic operations
        test_key = "health_check_test"
        test_value = {"test": True, "timestamp": time.time()}
        
        # Test set operation
        await cache_service.set(
            text=test_key,
            params={},
            result=test_value,
            ttl=10
        )
        
        # Test get operation
        retrieved = await cache_service.get(test_key, {})
        
        # Test delete operation
        await cache_service.delete(test_key, {})
        
        # Get cache stats
        stats = await cache_service.get_stats()
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return ServiceStatus(
            status=HEALTH_STATUS_HEALTHY,
            response_time_ms=response_time_ms,
            details={
                "redis_url": settings.redis_url,
                "namespace": "health_check",
                "stats": stats
            }
        )
        
    except Exception as e:
        logger.warning(
            "cache_service_health_check_failed",
            error=str(e),
            redis_url=settings.redis_url
        )
        
        return ServiceStatus(
            status=HEALTH_STATUS_UNHEALTHY,
            response_time_ms=int((time.time() - start_time) * 1000),
            error=str(e),
            details={
                "redis_url": settings.redis_url
            }
        )


async def check_evaluation_service(settings: SettingsDep) -> ServiceStatus:
    """
    Check evaluation service health.
    
    Tests the evaluation service to ensure it's available
    for quality assessment operations.
    
    Args:
        settings: Application settings
        
    Returns:
        ServiceStatus with evaluation service health information
    """
    start_time = time.time()
    
    try:
        # Create evaluator instance
        evaluator = SummaryEvaluator(model_name=settings.evaluation_model)
        
        # Test evaluation with sample data
        original_text = "This is a test text for evaluation."
        summary_text = "Test summary for evaluation."
        
        evaluation = evaluator.evaluate(original_text, summary_text)
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return ServiceStatus(
            status=HEALTH_STATUS_HEALTHY,
            response_time_ms=response_time_ms,
            details={
                "model": settings.evaluation_model,
                "test_quality_score": evaluation["quality_score"]
            }
        )
        
    except Exception as e:
        logger.warning(
            "evaluation_service_health_check_failed",
            error=str(e),
            model=settings.evaluation_model
        )
        
        return ServiceStatus(
            status=HEALTH_STATUS_UNHEALTHY,
            response_time_ms=int((time.time() - start_time) * 1000),
            error=str(e),
            details={
                "model": settings.evaluation_model
            }
        )


@router.get(
    "/healthz",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="""
    Comprehensive health check for all service components.
    
    **Checks performed:**
    - LLM Provider connectivity and functionality
    - Cache service (Redis) connectivity and operations
    - Evaluation service availability and functionality
    
    **Response includes:**
    - Overall service status
    - Individual service health details
    - Response times for each service
    - Error information for failed services
    - Service version and uptime information
    
    **Status levels:**
    - **healthy**: All services operational
    - **degraded**: Some services have issues but core functionality works
    - **unhealthy**: Critical services are unavailable
    """,
    responses={
        200: {
            "description": "Health check completed",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": 1640995200.123,
                        "services": {
                            "llm_provider": {
                                "status": "healthy",
                                "response_time_ms": 150,
                                "details": {"model": "gemini-pro"}
                            },
                            "redis": {
                                "status": "healthy",
                                "response_time_ms": 5,
                                "details": {"connected_clients": 10}
                            }
                        },
                        "version": "1.0.0",
                        "uptime_seconds": 86400.0
                    }
                }
            }
        },
        503: {"description": "Service unhealthy"}
    },
    tags=["Health"]
)
async def health_check(
    settings: SettingsDep
) -> HealthResponse:
    """
    Perform comprehensive health check of all service components.
    
    Tests the health and availability of all critical service components
    including LLM providers, cache services, and evaluation services.
    Provides detailed status information for monitoring and debugging.
    
    Args:
        settings: Application settings
        
    Returns:
        HealthResponse with comprehensive health status
        
    Raises:
        HTTPException: If critical services are unhealthy
    """
    start_time = time.time()
    
    logger.info("health_check_started")
    
    try:
        # Check all services
        services = {}
        
        # Check LLM provider
        llm_status = await check_llm_provider(settings)
        services["llm_provider"] = llm_status
        
        # Check cache service
        cache_status = await check_cache_service(settings)
        services["redis"] = cache_status
        
        # Check evaluation service
        if settings.enable_auto_evaluation:
            eval_status = await check_evaluation_service(settings)
            services["evaluation_service"] = eval_status
        
        # Determine overall status
        unhealthy_services = [
            name for name, status in services.items()
            if status.status == HEALTH_STATUS_UNHEALTHY
        ]
        
        degraded_services = [
            name for name, status in services.items()
            if status.status == HEALTH_STATUS_DEGRADED
        ]
        
        if unhealthy_services:
            overall_status = HEALTH_STATUS_UNHEALTHY
        elif degraded_services:
            overall_status = HEALTH_STATUS_DEGRADED
        else:
            overall_status = HEALTH_STATUS_HEALTHY
        
        # Build response
        response = HealthResponse(
            status=overall_status,
            timestamp=time.time(),
            services=services,
            version=settings.api_version,
            uptime_seconds=time.time() - start_time  # Simplified uptime
        )
        
        # Log health check results
        logger.info(
            "health_check_completed",
            overall_status=overall_status,
            unhealthy_services=unhealthy_services,
            degraded_services=degraded_services,
            total_services=len(services)
        )
        
        # Return appropriate status code
        if overall_status == HEALTH_STATUS_UNHEALTHY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service unhealthy / Servicio no saludable"
            )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.exception(
            "health_check_failed",
            error=str(e)
        )
        
        # Return unhealthy status for unexpected errors
        return HealthResponse(
            status=HEALTH_STATUS_UNHEALTHY,
            timestamp=time.time(),
            services={
                "system": ServiceStatus(
                    status=HEALTH_STATUS_UNHEALTHY,
                    error=str(e),
                    details={"error_type": "unexpected_error"}
                )
            },
            version=settings.api_version,
            uptime_seconds=time.time() - start_time
        )


# Export for easy importing
__all__ = ["router"]
