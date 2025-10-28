"""
Main API router for v1 endpoints.

Combines all API routers into a single router with proper
prefix configuration and comprehensive documentation.
"""

from fastapi import APIRouter

from app.api.v1.summarize import router as summarize_router
from app.api.v1.health import router as health_router

# Create main v1 router
router = APIRouter(
    prefix="/v1",
    tags=["v1"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)

# Include sub-routers
router.include_router(summarize_router)
router.include_router(health_router)

# Export for easy importing
__all__ = ["router"]