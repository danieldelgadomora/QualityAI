from fastapi import APIRouter
from app.config import settings
from app.dependencies import is_agent_ready

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "agent_ready": is_agent_ready(),
        "model": "qwen/qwen3-32b",
        "max_concurrent_jobs": settings.max_concurrent_jobs,
    }
