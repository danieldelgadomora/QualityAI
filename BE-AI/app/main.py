from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies import init_agent
from app.routers import health, hitl, requirements


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_agent()
    yield


app = FastAPI(
    title="QualityAI Backend",
    description="API para el agente de refinamiento de requerimientos v3 (RAG + Ambigüedades)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(requirements.router, prefix="/api/v1")
app.include_router(hitl.router, prefix="/api/v1")
