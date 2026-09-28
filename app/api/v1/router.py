"""Main API v1 Router aggregating all v1 endpoints (`/api/v1`)."""

from fastapi import APIRouter

from app.api.v1.exams import router as exams_router
from app.api.v1.payments import router as payments_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(exams_router)
api_v1_router.include_router(payments_router)

# Alias `router` for convenience
router = api_v1_router

__all__ = ["api_v1_router", "router"]
