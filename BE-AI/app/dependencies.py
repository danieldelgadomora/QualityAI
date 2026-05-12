import os
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from app.config import settings

# Garantizar que GROQ_API_KEY esté en os.environ antes del import del agente.
# agente_v3_ambiguity.py tiene un check a nivel de módulo que llama sys.exit(1)
# si la variable no está disponible en el momento del import.
os.environ.setdefault("GROQ_API_KEY", settings.groq_api_key)

if settings.agent_module_path not in sys.path:
    sys.path.insert(0, settings.agent_module_path)

from agente_v1_rag import pipeline_rag as _pipeline_rag_v1  # noqa: E402
from agente_v2_json import RequirementsRefinerAgent as _AgentV2  # noqa: E402
from agente_v3_ambiguity import RequirementsRefinerAgent as _AgentV3  # noqa: E402
from app.agents.hitl_adapter import APIRequirementsRefinerAgent as _AgentV4  # noqa: E402

_agent_v3: Optional[_AgentV3] = None
_agent_v2: Optional[_AgentV2] = None
_agent_v4: Optional[_AgentV4] = None
_executor: Optional[ThreadPoolExecutor] = None


def init_agent() -> None:
    global _agent_v3, _agent_v2, _agent_v4, _executor
    print("⏳ Inicializando agente v3...")
    _agent_v3 = _AgentV3(groq_api_key=settings.groq_api_key)
    print("✅ Agente v3 listo")
    print("⏳ Inicializando agente v2...")
    _agent_v2 = _AgentV2(groq_api_key=settings.groq_api_key)
    print("✅ Agente v2 listo")
    print("⏳ Inicializando agente v4 (HITL)...")
    _agent_v4 = _AgentV4(groq_api_key=settings.groq_api_key)
    print("✅ Agente v4 listo")
    _executor = ThreadPoolExecutor(max_workers=settings.max_concurrent_jobs)


def get_agent() -> _AgentV3:
    if _agent_v3 is None:
        raise RuntimeError("Agente v3 no inicializado")
    return _agent_v3


def get_agent_v2() -> _AgentV2:
    if _agent_v2 is None:
        raise RuntimeError("Agente v2 no inicializado")
    return _agent_v2


def get_agent_v4() -> _AgentV4:
    if _agent_v4 is None:
        raise RuntimeError("Agente v4 no inicializado")
    return _agent_v4


def get_pipeline_rag_v1():
    return _pipeline_rag_v1


def get_executor() -> ThreadPoolExecutor:
    if _executor is None:
        raise RuntimeError("Executor no inicializado")
    return _executor


def is_agent_ready() -> bool:
    return _agent_v3 is not None
