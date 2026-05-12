import asyncio
import functools
from datetime import datetime

from app.dependencies import get_agent_v4, get_executor
from app.schemas.response import JobStatusEnum
from app.services import job_store

# Garantiza que solo un process_with_resolutions corra a la vez sobre el
# agente compartido, evitando colisiones en _injected_resolutions.
# asyncio.Lock cede el control al event loop mientras espera, a diferencia
# de threading.Lock que bloquearía todo el hilo del event loop.
_v4_lock = asyncio.Lock()


async def run_agent_v4(
    run_id: str,
    requirement_text: str,
    top_k: int,
    resolutions: list[dict],
) -> None:
    job_store.update_job(run_id, status=JobStatusEnum.PROCESSING)

    loop = asyncio.get_running_loop()
    async with _v4_lock:
        agent = get_agent_v4()
        try:
            result = await loop.run_in_executor(
                get_executor(),
                functools.partial(
                    agent.process_with_resolutions,
                    requirement_text,
                    top_k,
                    resolutions,
                ),
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
