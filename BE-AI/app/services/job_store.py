import threading
from datetime import datetime
from typing import Optional

from app.schemas.response import JobResponse, JobStatusEnum

_store: dict[str, JobResponse] = {}
_lock = threading.Lock()


def create_job(run_id: str, requirement_text: str) -> JobResponse:
    preview = requirement_text[:100] + ("..." if len(requirement_text) > 100 else "")
    job = JobResponse(
        run_id=run_id,
        status=JobStatusEnum.PENDING,
        created_at=datetime.now(),
        requirement_preview=preview,
    )
    with _lock:
        _store[run_id] = job
    return job


def update_job(run_id: str, **kwargs) -> Optional[JobResponse]:
    with _lock:
        job = _store.get(run_id)
        if job is None:
            return None
        updated = job.model_copy(update=kwargs)
        _store[run_id] = updated
        return updated


def get_job(run_id: str) -> Optional[JobResponse]:
    with _lock:
        return _store.get(run_id)


def list_jobs(limit: int = 20) -> list[JobResponse]:
    with _lock:
        jobs = sorted(_store.values(), key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]
