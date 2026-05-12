"""Orquestador del pipeline M1+M2 sobre WebSocket.

Reemplaza todos los input() de pipeline_auto.py con rendezvous asyncio.Queue,
permitiendo que la interactividad ocurra desde el navegador en vez del CLI.
"""
import asyncio
import dataclasses
import functools
import sys
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Type, TypeVar

from app.dependencies import get_agent_v4, get_executor, get_m2_kb
from app.schemas.pipeline_ws import (
    GlobalDecisionMsg,
    ResolveAmbiguitiesMsg,
    ReviewerIdMsg,
    ScenarioActionMsg,
    StartPipelineMsg,
)
from app.services.hitl_agent_service import _v4_lock

# Agregar el raíz de QualityAI al path para importar los módulos del pipeline
_QUALITYAI_ROOT = Path(__file__).resolve().parents[3]
if str(_QUALITYAI_ROOT) not in sys.path:
    sys.path.insert(0, str(_QUALITYAI_ROOT))

from groq import Groq  # noqa: E402

from modulo2_test_architect.pipeline_auto import (  # noqa: E402
    buscar_patrones_similares,
    construir_contract_b,
    construir_prompt,
    generar_con_groq,
    guardar_contract_b_revisado,
    parsear_a_escenarios,
    recalcular_matriz,
)
from modulo2_test_architect.generate_acta import guardar_acta  # noqa: E402
from modulo2_test_architect.src.contract_b import (  # noqa: E402
    QualityCharacteristic,
    ReviewChange,
    ReviewStatus,
)

from app.config import settings  # noqa: E402

T = TypeVar("T")


class PipelineOrchestrator:
    """Una instancia por conexión WebSocket.

    send_queue: la corrutina pone dicts aquí; el router los drena a ws.send_text().
    recv_queue: el router pone InboundMessage aquí; la corrutina espera con _recv_typed().
    """

    def __init__(self):
        self.send_queue: asyncio.Queue[dict | None] = asyncio.Queue()
        self.recv_queue: asyncio.Queue = asyncio.Queue()

    async def _send(self, msg: dict) -> None:
        await self.send_queue.put(msg)

    async def _recv_typed(self, expected: Type[T]) -> T:
        """Bloquea hasta recibir un mensaje del tipo Pydantic esperado.

        Mensajes de tipo incorrecto se descartan silenciosamente.
        En desarrollo, React StrictMode puede enviar duplicados de
        start_pipeline; ignorarlos aquí evita terminar el pipeline con error.
        """
        while True:
            msg = await self.recv_queue.get()
            if isinstance(msg, expected):
                return msg
            # Descartar mensaje fuera de orden y seguir esperando

    async def run(self) -> None:
        """Punto de entrada; captura cualquier excepción no manejada."""
        try:
            await self._run_pipeline()
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            await self._send({
                "type": "pipeline_error",
                "message": str(exc),
                "phase": "unknown",
            })
        finally:
            await self.send_queue.put(None)  # señal de fin para el drain-loop

    # ── PIPELINE PRINCIPAL ──────────────────────────────────────────────────
    async def _run_pipeline(self) -> None:
        loop = asyncio.get_running_loop()
        executor = get_executor()

        # ── Esperar kick-off del cliente ────────────────────────────────────
        start_msg: StartPipelineMsg = await self._recv_typed(StartPipelineMsg)

        # ── FASE 0 — M1: Refinamiento de requerimiento ──────────────────────
        await self._send({
            "type": "status_update",
            "message": "Detectando ambigüedades en el requerimiento...",
            "phase": "m1",
        })

        agent_v4 = get_agent_v4()
        ambiguities = await loop.run_in_executor(
            executor,
            functools.partial(agent_v4.ambiguity_detector.analyze, start_msg.requirement_text),
        )

        resolutions: list[dict] = []
        if ambiguities and start_msg.interactive_m1:
            await self._send({
                "type": "m1_ambiguities_detected",
                "ambiguities": [dataclasses.asdict(a) for a in ambiguities],
            })
            resolve_msg: ResolveAmbiguitiesMsg = await self._recv_typed(ResolveAmbiguitiesMsg)
            resolutions = [r.model_dump() for r in resolve_msg.resolutions]

        await self._send({
            "type": "status_update",
            "message": "Generando Contract A con el LLM...",
            "phase": "m1",
        })

        async with _v4_lock:
            contract_a = await loop.run_in_executor(
                executor,
                functools.partial(
                    agent_v4.process_with_resolutions,
                    start_msg.requirement_text,
                    start_msg.top_k,
                    resolutions,
                ),
            )

        await self._send({
            "type": "m1_completed",
            "contract_a": contract_a.model_dump(mode="json"),
        })

        # ── FASE 1 — M2: Generación de escenarios Gherkin ───────────────────
        modelo, collection = get_m2_kb()
        groq_client = Groq(api_key=settings.groq_api_key)

        total_acs = sum(len(s.acceptance_criteria) for s in contract_a.user_stories)
        done_acs = 0
        scenarios_por_story: dict[str, list] = {}

        for story in contract_a.user_stories:
            scenarios_por_story[story.id] = []
            for ac in story.acceptance_criteria:
                await self._send({
                    "type": "status_update",
                    "message": f"Generando escenarios para {ac.id} ({story.title[:30]}...)...",
                    "phase": "m2_gen",
                })

                patrones = await loop.run_in_executor(
                    executor,
                    functools.partial(buscar_patrones_similares, modelo, collection, ac, 3),
                )
                sys_prompt, usr_msg = construir_prompt(ac, story, patrones)
                raw = await loop.run_in_executor(
                    executor,
                    functools.partial(generar_con_groq, groq_client, sys_prompt, usr_msg),
                )

                try:
                    escenarios = await loop.run_in_executor(
                        executor,
                        functools.partial(parsear_a_escenarios, raw, ac, story),
                    )
                    scenarios_por_story[story.id].extend(escenarios)
                    generated = len(escenarios)
                except Exception:
                    generated = 0

                done_acs += 1
                await self._send({
                    "type": "m2_progress",
                    "ac_id": ac.id,
                    "story_id": story.id,
                    "scenarios_generated": generated,
                    "total_acs": total_acs,
                    "done_acs": done_acs,
                })

        suite = await loop.run_in_executor(
            executor,
            functools.partial(construir_contract_b, contract_a, scenarios_por_story),
        )

        await self._send({
            "type": "m2_completed",
            "total_scenarios": suite.total_scenarios,
        })

        # ── FASE 2 — Revisión humana: pedir ID del revisor ──────────────────
        await self._send({
            "type": "scenario_review_prompt",
            "scenario_index": -1,
            "total_scenarios": suite.total_scenarios,
            "scenario": None,
        })
        reviewer_msg: ReviewerIdMsg = await self._recv_typed(ReviewerIdMsg)
        reviewer = reviewer_msg.reviewer

        # ── Revisión escenario por escenario ────────────────────────────────
        todos = [s for f in suite.features for s in f.scenarios]
        history: list[ReviewChange] = []
        matriz_original = deepcopy(suite.coverage_by_characteristic)

        for idx, scenario in enumerate(todos):
            await self._send({
                "type": "scenario_review_prompt",
                "scenario_index": idx,
                "total_scenarios": len(todos),
                "scenario": scenario.model_dump(mode="json"),
            })
            action_msg: ScenarioActionMsg = await self._recv_typed(ScenarioActionMsg)

            if action_msg.action == "accept":
                history.append(ReviewChange(
                    reviewer=reviewer,
                    action="accepted",
                    notes=f"'{scenario.name}': clasificación '{scenario.quality_characteristic.value}' confirmada.",
                ))
            elif action_msg.action == "reclassify" and action_msg.new_quality_characteristic:
                new_qc = QualityCharacteristic(action_msg.new_quality_characteristic)
                old_qc = scenario.quality_characteristic.value
                scenario.quality_characteristic = new_qc
                scenario.tags = [t for t in scenario.tags if not t.lower().startswith("@iso-")]
                scenario.tags.append(f"@iso-{new_qc.value.replace('_', '-')}")
                history.append(ReviewChange(
                    reviewer=reviewer,
                    action="reclassified",
                    notes=f"'{scenario.name}': {old_qc} → {new_qc.value}. Razón: {action_msg.note or '(sin nota)'}",
                ))
            elif action_msg.action == "comment":
                history.append(ReviewChange(
                    reviewer=reviewer,
                    action="comment_added",
                    notes=f"'{scenario.name}': {action_msg.note or ''}",
                ))
            # "skip" no registra entrada en el historial

        recalcular_matriz(suite)

        await self._send({
            "type": "global_decision_prompt",
            "reclassifications": sum(1 for h in history if h.action == "reclassified"),
            "coverage_before": matriz_original,
            "coverage_after": suite.coverage_by_characteristic,
        })

        decision_msg: GlobalDecisionMsg = await self._recv_typed(GlobalDecisionMsg)
        _apply_global_decision(suite, reviewer, decision_msg, history)
        suite.review.change_history.extend(history)

        # ── FASE 3 — Guardar resultados ─────────────────────────────────────
        await self._send({
            "type": "status_update",
            "message": "Guardando Contract B revisado...",
            "phase": "saving",
        })

        output_dir = _QUALITYAI_ROOT / "modulo2_test_architect" / "output"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        contract_b_path = await loop.run_in_executor(
            executor,
            functools.partial(guardar_contract_b_revisado, suite, output_dir, timestamp),
        )

        acta_html: str | None = None
        if suite.review.review_status == ReviewStatus.APPROVED:
            await self._send({
                "type": "status_update",
                "message": "Generando Acta de Aprobación HTML...",
                "phase": "saving",
            })
            acta_path = await loop.run_in_executor(
                executor,
                functools.partial(guardar_acta, suite, contract_b_path),
            )
            acta_html = acta_path.read_text(encoding="utf-8")

        await self._send({
            "type": "pipeline_completed",
            "status": suite.review.review_status.value,
            "contract_b_run_id": suite.pipeline_run_id,
            "total_scenarios": suite.total_scenarios,
            "acta_html": acta_html,
        })


def _apply_global_decision(
    suite,
    reviewer: str,
    msg: GlobalDecisionMsg,
    history: list[ReviewChange],
) -> None:
    """Aplica la decisión global al suite (equivale a decision_global() sin input())."""
    action_map = {
        "approve": ("approved", ReviewStatus.APPROVED),
        "reject": ("rejected", ReviewStatus.REJECTED),
        "request_changes": ("changes_requested", ReviewStatus.NEEDS_CHANGES),
    }
    action, status = action_map[msg.decision]
    suite.review.review_status = status
    if msg.decision == "approve":
        suite.review.approved_by = reviewer
        suite.review.approved_at = datetime.now()
    elif msg.decision == "request_changes":
        suite.review.version += 1
    if msg.feedback:
        suite.review.analyst_feedback = msg.feedback
    history.append(ReviewChange(
        reviewer=reviewer,
        action=action,
        notes=msg.feedback or f"Decisión final: {status.value}",
    ))
