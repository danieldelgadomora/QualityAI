import asyncio
import functools
from datetime import datetime

from app.dependencies import get_agent, get_agent_v2, get_executor, get_pipeline_rag_v1
from app.schemas.response import JobStatusEnum
from app.services import job_store


async def run_agent(run_id: str, requirement_text: str, top_k: int) -> None:
    job_store.update_job(run_id, status=JobStatusEnum.PROCESSING)

    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(
            get_executor(),
            functools.partial(get_agent().process, requirement_text, top_k),
        )
        job_store.update_job(
            run_id,
            status=JobStatusEnum.COMPLETED,
            completed_at=datetime.now(),
            result=result.model_dump(mode="json"),
        )
    except Exception as exc:
        job_store.update_job(
            run_id,
            status=JobStatusEnum.FAILED,
            completed_at=datetime.now(),
            error=str(exc),
        )


async def run_agent_v1(requirement_text: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        get_executor(),
        functools.partial(get_pipeline_rag_v1(), requirement_text),
    )


async def run_agent_v2(run_id: str, requirement_text: str, top_k: int) -> None:
    job_store.update_job(run_id, status=JobStatusEnum.PROCESSING)

    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(
            get_executor(),
            functools.partial(get_agent_v2().process, requirement_text, top_k),
        )
        job_store.update_job(
            run_id,
            status=JobStatusEnum.COMPLETED,
            completed_at=datetime.now(),
            result=result.model_dump(mode="json"),
        )
    except Exception as exc:
        job_store.update_job(
            run_id,
            status=JobStatusEnum.FAILED,
            completed_at=datetime.now(),
            error=str(exc),
        )
