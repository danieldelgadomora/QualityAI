import dataclasses
import uuid

from fastapi import APIRouter, HTTPException

from app.dependencies import get_agent_v4
from app.schemas.hitl import AmbiguityItem, HitlResolveRequest, HitlStartResponse
from app.schemas.request import AnalyzeRequest
from app.schemas.response import JobResponse
from app.services import hitl_agent_service, job_store
from app.services.hitl_session_store import consume_session, create_session

router = APIRouter(prefix="/hitl", tags=["hitl"])


@router.post("/start", response_model=HitlStartResponse)
async def hitl_start(body: AnalyzeRequest):
    """Fase 1: detecta ambigüedades y crea la sesión HITL.

    La detección es regex puro (sin LLM), por lo que responde en milisegundos.
    El cliente muestra las ambigüedades al analista y recoge sus decisiones
    antes de llamar a /resolve.
    """
    agent = get_agent_v4()
    ambiguities = agent.ambiguity_detector.analyze(body.requirement_text)
    ambiguity_dicts = [dataclasses.asdict(a) for a in ambiguities]

    session_id = f"sess-{uuid.uuid4().hex[:12]}"
    create_session(session_id, body.requirement_text, body.top_k, ambiguity_dicts)

    preview = body.requirement_text[:100] + (
        "..." if len(body.requirement_text) > 100 else ""
    )

    return HitlStartResponse(
        session_id=session_id,
        requirement_preview=preview,
        ambiguity_count=len(ambiguities),
        ambiguities=[AmbiguityItem(**a) for a in ambiguity_dicts],
        requires_review=len(ambiguities) > 0,
    )


@router.post("/resolve", response_model=JobResponse)
async def hitl_resolve(body: HitlResolveRequest):
    """Fase 2: ejecuta el pipeline completo con las resoluciones del analista.

    Retorna el mismo JobResponse que /agente2 y /agente3, con result conteniendo
    el RefinedRequirements generado sin suposiciones del LLM.
    """
    session = consume_session(body.session_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail=f"Sesión '{body.session_id}' no encontrada, expirada o ya consumida.",
        )

    detected = {a["word"] for a in session.ambiguities}
    provided = {r.word for r in body.resolutions}
    missing = detected - provided
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Faltan resoluciones para: {sorted(missing)}",
        )

    run_id = f"run-{uuid.uuid4().hex[:8]}"
    job_store.create_job(run_id, session.requirement_text)

    await hitl_agent_service.run_agent_v4(
        run_id=run_id,
        requirement_text=session.requirement_text,
        top_k=session.top_k,
        resolutions=[r.model_dump() for r in body.resolutions],
    )

    return job_store.get_job(run_id)
