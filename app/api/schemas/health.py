"""
Pydantic schemas for health check API endpoints.

Defines request and response models for health monitoring
with comprehensive service status information.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from app.core.constants import (
    HEALTH_STATUS_HEALTHY,
    HEALTH_STATUS_DEGRADED,
    HEALTH_STATUS_UNHEALTHY,
)


class ServiceStatus(BaseModel):
    """
    Individual service health status.
    
    Provides detailed health information for a specific service
    including status, response time, and any error details.
    
    Attributes:
        status: Service health status
        response_time_ms: Response time in milliseconds
        error: Optional error message if service is unhealthy
        details: Additional service-specific information
    """
    
    status: str = Field(
        ...,
        description="Service health status",
        examples=[HEALTH_STATUS_HEALTHY, HEALTH_STATUS_DEGRADED, HEALTH_STATUS_UNHEALTHY]
    )
    
    response_time_ms: Optional[int] = Field(
        None,
        ge=0,
        description="Service response time in milliseconds",
        example=150
    )
    
    error: Optional[str] = Field(
        None,
        description="Error message if service is unhealthy",
        example="Connection timeout"
    )
    
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional service-specific information",
        example={"version": "1.0.0", "uptime": "24h"}
    )


class HealthResponse(BaseModel):
    """
    Health check response model.
    
    Provides comprehensive health status for the entire service
    including individual service statuses and overall system health.
    
    Attributes:
        status: Overall service health status
        timestamp: Health check timestamp
        services: Individual service health statuses
        version: API version
        uptime_seconds: Service uptime in seconds
    """
    
    status: str = Field(
        ...,
        description="Overall service health status",
        examples=[HEALTH_STATUS_HEALTHY, HEALTH_STATUS_DEGRADED, HEALTH_STATUS_UNHEALTHY]
    )
    
    timestamp: float = Field(
        ...,
        description="Health check timestamp (Unix timestamp)",
        example=1640995200.123
    )
    
    services: Dict[str, ServiceStatus] = Field(
        ...,
        description="Health status of individual services",
        example={
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
        }
    )
    
    version: str = Field(
        ...,
        description="API version",
        example="1.0.0"
    )
    
    uptime_seconds: Optional[float] = Field(
        None,
        description="Service uptime in seconds",
        example=86400.0
    )
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": 1640995200.123,
                "services": {
                    "llm_provider": {
                        "status": "healthy",
                        "response_time_ms": 150,
                        "details": {
                            "model": "gemini-pro",
                            "provider": "gemini"
                        }
                    },
                    "redis": {
                        "status": "healthy",
                        "response_time_ms": 5,
                        "details": {
                            "connected_clients": 10,
                            "memory_usage": "2.5MB"
                        }
                    },
                    "evaluation_service": {
                        "status": "healthy",
                        "response_time_ms": 200,
                        "details": {
                            "model": "all-MiniLM-L6-v2"
                        }
                    }
                },
                "version": "1.0.0",
                "uptime_seconds": 86400.0
            }
        }


# Export for easy importing
__all__ = [
    "ServiceStatus",
    "HealthResponse",
]
