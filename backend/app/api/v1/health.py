"""Health check endpoint — used by Docker/CI to verify the service is up."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    return {"success": True, "data": {"status": "ok"}}
