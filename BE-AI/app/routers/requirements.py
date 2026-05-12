import uuid
from fastapi import APIRouter, HTTPException, Query

from app.schemas.request import AnalyzeRequest
from app.schemas.response import AgentV1Response, JobResponse, JobSummary
from app.services import agent_service, job_store

router = APIRouter(prefix="/requirements", tags=["requirements"])


@router.post("/agente1", response_model=AgentV1Response)
async def analizar_agente1(body: AnalyzeRequest):
    result_text = await agent_service.run_agent_v1(body.requirement_text)
    return AgentV1Response(result_text=result_text)


@router.post("/agente2", response_model=JobResponse)
async def analizar_agente2(body: AnalyzeRequest):
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    job_store.create_job(run_id, body.requirement_text)
    await agent_service.run_agent_v2(run_id, body.requirement_text, body.top_k)
    return job_store.get_job(run_id)


@router.post("/agente3", response_model=JobResponse)
async def analizar_agente3(body: AnalyzeRequest):
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    job_store.create_job(run_id, body.requirement_text)
    await agent_service.run_agent(run_id, body.requirement_text, body.top_k)
    return job_store.get_job(run_id)


@router.get("/", response_model=list[JobSummary])
def list_requirements(limit: int = Query(default=20, ge=1, le=100)):
    return job_store.list_jobs(limit)


@router.get("/{run_id}", response_model=JobResponse)
def get_requirement(run_id: str):
    job = job_store.get_job(run_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{run_id}' no encontrado")
    return job
