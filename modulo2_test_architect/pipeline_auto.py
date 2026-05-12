"""Pipeline M2: Generación automática + Revisión humana + Acta.

Combina en un único script:
  · agente_v3_iso25010.py  — genera escenarios Gherkin clasificados con ISO 25010
  · review_cli.py          — revisión humana escenario por escenario, decisión final
  · generate_acta.py       — produce el Acta HTML lista para entregar al cliente

Uso:
    python pipeline_auto.py
    python pipeline_auto.py <ruta_contract_a.json>
    python pipeline_auto.py <ruta_contract_a.json> --output-dir ./output

Flujo:
    Contract A (JSON)
        → Generación: RAG + EP/BVA/DT + ISO 25010 → Groq → Contract B
        → Revisión humana: escenario por escenario (a/r/c/s/q) + decisión global
        → Guardar Contract B revisado (_reviewed.json)
        → Generar Acta de Aprobación HTML (_acta.html)
"""

import argparse
import json
import os
import sys
import uuid
import warnings
from collections import Counter
from copy import deepcopy
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore")

from dotenv import load_dotenv
from groq import Groq
from pydantic import ValidationError
from sentence_transformers import SentenceTransformer
import chromadb

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from modulo2_test_architect.src.contract_a_input import (
    AcceptanceCriterion,
    RefinedRequirements,
    UserStory,
)
from modulo2_test_architect.src.contract_b import (
    CoverageMatrix,
    GherkinFeature,
    GherkinScenario,
    GherkinStep,
    GherkinTestSuite,
    QualityCharacteristic,
    ReviewChange,
    ReviewStatus,
    ScenarioType,
)
from modulo2_test_architect.generate_acta import guardar_acta

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("Error: No se encontró GROQ_API_KEY en el archivo .env")
    sys.exit(1)

# Importar el agente de refinamiento de requerimientos (Módulo 1)
# Se añade su directorio raíz al path para que sus imports relativos resuelvan.
_M1_ROOT = Path(__file__).resolve().parents[1] / "modulo1_requirements_refiner"
if str(_M1_ROOT) not in sys.path:
    sys.path.insert(0, str(_M1_ROOT))

from agente_v4_hitl import RequirementsRefinerAgent  # noqa: E402


# ============================================================
# UTILIDADES DE CONSOLA
# ============================================================
def _sep(char: str = "=", n: int = 70):
    print(char * n)


def _titulo(texto: str):
    print()
    _sep()
    print(f" {texto}")
    _sep()


def leer_input(prompt: str, default: str = "", obligatorio: bool = False) -> str:
    """Lee input del usuario con manejo limpio de Ctrl+C / EOF."""
    while True:
        try:
            valor = input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[Sesión interrumpida — el suite queda en pending_review]")
            sys.exit(0)
        if not valor and default:
            return default
        if not valor and obligatorio:
            print("   Este campo es obligatorio. Intenta de nuevo.")
            continue
        return valor


# ============================================================
# FASE 0: REFINAMIENTO DEL REQUERIMIENTO (M1 — agente_v4_hitl)
# ============================================================
def fase_refinamiento() -> tuple[RefinedRequirements, Path]:
    """Recibe texto libre del usuario, resuelve ambigüedades (HITL) y genera el Contract A."""
    _titulo("FASE 0 — INGRESO Y REFINAMIENTO DEL REQUERIMIENTO (M1)")
    print(" Escribe el requerimiento en lenguaje natural.")
    print(" El agente detectará términos ambiguos y te pedirá resolverlos antes de continuar.")
    print()

    requerimiento = leer_input("Requerimiento:\n> ", obligatorio=True)

    print()
    print(" Modo de revisión de ambigüedades:")
    print("   [1] Interactivo — el analista resuelve cada ambigüedad (recomendado)")
    print("   [2] Automático  — el LLM asume suposiciones sin consultar")
    modo = leer_input("\n Elige modo [1/2] (Enter = 1): ", default="1")
    interactive = (modo.strip() != "2")

    print()
    agente_m1 = RequirementsRefinerAgent(groq_api_key=GROQ_API_KEY)
    contract_a = agente_m1.process(requerimiento, interactive=interactive)

    # Guardar Contract A para trazabilidad del pipeline
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    contract_a_path = output_dir / f"contract_a_pipeline_{timestamp}.json"
    contract_a_path.write_text(contract_a.model_dump_json(indent=2), encoding="utf-8")

    _sep()
    print(f"   Contract A generado:      {contract_a_path.name}")
    print(f"   Historias de usuario:     {len(contract_a.user_stories)}")
    total_ac = sum(len(s.acceptance_criteria) for s in contract_a.user_stories)
    print(f"   Criterios de aceptación:  {total_ac}")
    print(f"   Suposiciones del LLM:     {contract_a.total_assumptions_made}")
    _sep()

    return contract_a, contract_a_path


# ============================================================
# GENERACIÓN — PASO 1: Cargar Contract A desde JSON (retro-compatible)
# ============================================================
def cargar_contract_a(path: str) -> RefinedRequirements:
    print(f"\nPASO 1: Cargando Contract A desde {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    contract_a = RefinedRequirements(**data)
    total_ac = sum(len(s.acceptance_criteria) for s in contract_a.user_stories)
    print(f"   Pipeline ID:              {contract_a.pipeline_run_id}")
    print(f"   Historias de usuario:     {len(contract_a.user_stories)}")
    print(f"   Criterios de aceptación:  {total_ac}")
    return contract_a


# ============================================================
# GENERACIÓN — PASO 2: Inicializar KB Katary (RAG)
# ============================================================
def inicializar_kb():
    print(f"\nPASO 2: Inicializando KB de patrones de testing Katary")
    print("   Cargando modelo de embeddings (all-MiniLM-L6-v2)...")
    modelo = SentenceTransformer("all-MiniLM-L6-v2")

    kb_path = Path(__file__).parent / "knowledge_base_data"
    client = chromadb.PersistentClient(path=str(kb_path))
    collection = client.get_or_create_collection(
        name="katary_test_patterns",
        metadata={"hnsw:space": "cosine"},
    )

    if collection.count() == 0:
        patterns_path = (
            Path(__file__).parent / "examples" / "knowledge_base" / "katary_test_patterns.json"
        )
        print(f"   Indexando patrones desde {patterns_path.name}...")
        with open(patterns_path, "r", encoding="utf-8") as f:
            patterns = json.load(f)
        textos = [
            f"{p['domain']}. {p['ac_pattern_typical']}. {p['katary_context']}"
            for p in patterns
        ]
        embeddings = modelo.encode(textos).tolist()
        collection.add(
            ids=[p["id"] for p in patterns],
            embeddings=embeddings,
            documents=textos,
            metadatas=[
                {
                    "domain": p["domain"],
                    "techniques_used": ", ".join(p["techniques_used"]),
                    "typical_scenarios": json.dumps(p["typical_scenarios"], ensure_ascii=False),
                    "lessons_learned_katary": p["lessons_learned_katary"],
                }
                for p in patterns
            ],
        )
        print(f"   {collection.count()} patrones indexados en ChromaDB")
    else:
        print(f"   KB existente: {collection.count()} patrones cargados")

    return modelo, collection


# ============================================================
# GENERACIÓN — PASO 3: Retrieval (buscar patrones similares)
# ============================================================
def buscar_patrones_similares(modelo, collection, ac: AcceptanceCriterion, top_k: int = 3):
    consulta = f"{ac.description}. Given {ac.given}. When {ac.when}. Then {ac.then}"
    emb = modelo.encode([consulta]).tolist()
    resultados = collection.query(
        query_embeddings=emb,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    patrones = []
    for i in range(len(resultados["ids"][0])):
        similitud = 1 - resultados["distances"][0][i]
        patrones.append(
            {
                "id": resultados["ids"][0][i],
                "domain": resultados["metadatas"][0][i]["domain"],
                "typical_scenarios": json.loads(resultados["metadatas"][0][i]["typical_scenarios"]),
                "lessons_learned_katary": resultados["metadatas"][0][i]["lessons_learned_katary"],
                "techniques_used": resultados["metadatas"][0][i]["techniques_used"],
                "similitud": similitud,
            }
        )
    return patrones


# ============================================================
# GENERACIÓN — PASO 4: Construir prompt (RAG + Heurísticas + ISO 25010)
# ============================================================
def construir_prompt(ac: AcceptanceCriterion, story: UserStory, patrones: list[dict]) -> tuple[str, str]:
    contexto_kb = "## PATRONES DE TESTING DEL SGC KATARY\n"
    contexto_kb += "Usa estos patrones como referencia de calidad para tus escenarios:\n\n"
    for i, p in enumerate(patrones, 1):
        contexto_kb += f"### Patron {i} [{p['id']}] dominio: {p['domain']} (similitud: {p['similitud']:.2f})\n"
        contexto_kb += f"Tecnicas usadas tipicamente: {p['techniques_used']}\n"
        contexto_kb += "Escenarios tipicos:\n"
        for s in p["typical_scenarios"]:
            contexto_kb += f"   - {s}\n"
        contexto_kb += f"Leccion Katary: {p['lessons_learned_katary']}\n\n"

    instrucciones_heuristicas = (
        "## INSTRUCCIONES DE TESTING DISCIPLINADO (OBLIGATORIAS)\n\n"
        "Para el criterio de aceptacion recibido, aplica las siguientes tecnicas\n"
        "de caja negra de manera explicita:\n\n"
        "1. EQUIVALENCE PARTITIONING (EP):\n"
        "   - Identifica las clases equivalentes validas e invalidas del AC.\n"
        "   - Genera UN escenario por cada clase identificada.\n"
        "   - Si el AC trae multiples test_data_examples, genera un escenario por cada uno.\n\n"
        "2. BOUNDARY VALUE ANALYSIS (BVA):\n"
        "   - Si el AC menciona un rango numerico, genera 4 escenarios adicionales:\n"
        "     limite inferior, justo debajo del inferior, limite superior, justo encima.\n"
        "   - Si el AC tiene boundary_values listados explicitamente, usalos.\n\n"
        "3. DECISION TABLES (DT):\n"
        "   - Si el AC tiene multiples condiciones que se combinan, genera UN escenario\n"
        "     por cada combinacion relevante.\n\n"
        "RESULTADO ESPERADO: minimo 1 positivo + 1 por cada clase invalida + BVA/DT si aplica.\n"
        "NO te conformes con UN escenario por AC.\n"
    )

    instrucciones_iso25010 = (
        "## CLASIFICACION ISO/IEC 25010 (OBLIGATORIA)\n\n"
        "Por cada escenario, asigna `quality_characteristic` con UNA de estas categorias:\n\n"
        "   - functional_suitability  (logica de negocio, validaciones, reglas, calculos)\n"
        "   - performance_efficiency  (tiempos de respuesta, carga concurrente)\n"
        "   - security                (autenticacion, autorizacion, bloqueo, cifrado, inyeccion)\n"
        "   - usability               (mensajes de error, accesibilidad, navegacion)\n"
        "   - reliability             (recuperacion de fallas, manejo de errores, timeouts)\n"
        "   - compatibility           (navegadores, SO, versiones, integraciones)\n"
        "   - maintainability         (rara vez aplica a BDD funcional)\n"
        "   - portability             (rara vez aplica a BDD funcional)\n\n"
        "Decide caso por caso. Bloqueo tras N intentos = security, no functional_suitability.\n"
    )

    system = (
        "Eres un Test Architect que convierte criterios de aceptacion en escenarios Gherkin (BDD)\n"
        "aplicando tecnicas de caja negra disciplinadas y clasificandolos segun ISO/IEC 25010.\n\n"
        f"{contexto_kb}\n{instrucciones_heuristicas}\n{instrucciones_iso25010}\n"
        "## FORMATO DE RESPUESTA OBLIGATORIO\n"
        "Devuelve UNICAMENTE un JSON valido:\n"
        '{"scenarios": [{"name": "...", "scenario_type": "positive|negative|boundary|edge_case|error_handling",\n'
        ' "quality_characteristic": "...", "tags": ["@tag"], "heuristic_applied": "EP|BVA|DT|general",\n'
        ' "steps": [{"keyword": "Given|When|Then|And", "text": "..."}]}]}\n'
        "Cada step.text >= 5 caracteres. Cada escenario declara heuristica y caracteristica ISO 25010.\n"
    )

    user = (
        f"Historia de usuario: {story.title}\n"
        f"Como {story.as_a}, quiero {story.i_want}, para {story.so_that}.\n\n"
        f"Criterio de aceptacion {ac.id}:\n"
        f"   Descripcion: {ac.description}\n"
        f"   Given: {ac.given}\n"
        f"   When: {ac.when}\n"
        f"   Then: {ac.then}\n"
        f"   Caso negativo: {'Si' if ac.is_negative_case else 'No'}\n"
        f"   Test data examples: {ac.test_data_examples}\n"
        f"   Boundary values: {ac.boundary_values}\n\n"
        "Genera la LISTA de escenarios Gherkin aplicando EP, BVA y/o DT según corresponda,\n"
        "y CLASIFICA cada escenario con su característica ISO/IEC 25010."
    )
    return system, user


# ============================================================
# GENERACIÓN — PASO 5: Llamar a Groq
# ============================================================
def generar_con_groq(client: Groq, system_prompt: str, user_message: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.0,
        seed=42,
        max_tokens=2500,
    )
    return response.choices[0].message.content


# ============================================================
# GENERACIÓN — PASO 6: Parsear respuesta del LLM
# ============================================================
def parsear_a_escenarios(raw_text: str, ac: AcceptanceCriterion, story: UserStory) -> list[GherkinScenario]:
    text = raw_text.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1].rsplit("```", 1)[0]
    elif "```" in text:
        text = text.split("```", 1)[1].rsplit("```", 1)[0]

    json_str = text[text.find("{") : text.rfind("}") + 1]
    data = json.loads(json_str)
    scenarios_data = data.get("scenarios", [])
    if not scenarios_data:
        raise ValueError(f"LLM no devolvió escenarios para AC {ac.id}")

    valid_qc = {qc.value for qc in QualityCharacteristic}
    escenarios = []
    for sd in scenarios_data:
        steps = [GherkinStep(keyword=s["keyword"], text=s["text"]) for s in sd["steps"]]
        tags = sd.get("tags", [])
        h = sd.get("heuristic_applied", "general")
        if h != "general" and f"@{h.lower()}" not in [t.lower() for t in tags]:
            tags.append(f"@{h.lower()}")

        qc_raw = sd.get("quality_characteristic", "functional_suitability")
        if qc_raw not in valid_qc:
            print(f"      Aviso: quality_characteristic inválida '{qc_raw}' — usando functional_suitability")
            qc_raw = "functional_suitability"
        qc = QualityCharacteristic(qc_raw)

        iso_tag = f"@iso-{qc.value.replace('_', '-')}"
        if iso_tag not in [t.lower() for t in tags]:
            tags.append(iso_tag)

        escenarios.append(GherkinScenario(
            name=sd["name"],
            scenario_type=ScenarioType(sd.get("scenario_type", "positive")),
            quality_characteristic=qc,
            tags=tags,
            steps=steps,
            acceptance_criterion_id=ac.id,
            user_story_id=story.id,
        ))
    return escenarios


# ============================================================
# GENERACIÓN — PASO 7: Calcular matriz de cobertura ISO 25010
# ============================================================
def calcular_matriz_cobertura(escenarios: list[GherkinScenario]) -> dict[str, int]:
    matriz = {qc.value: 0 for qc in QualityCharacteristic}
    matriz.update(Counter(e.quality_characteristic.value for e in escenarios))
    return matriz


# ============================================================
# GENERACIÓN — PASO 8: Construir Contract B
# ============================================================
def construir_contract_b(
    contract_a: RefinedRequirements,
    scenarios_por_story: dict[str, list[GherkinScenario]],
) -> GherkinTestSuite:
    print(f"\nPASO 8: Construyendo Contract B...")
    features = []
    for story in contract_a.user_stories:
        scenarios = scenarios_por_story.get(story.id, [])
        if not scenarios:
            print(f"   Aviso: historia {story.id} sin escenarios — saltando")
            continue
        features.append(GherkinFeature(
            name=story.title,
            description=f"Como {story.as_a}, quiero {story.i_want}, para {story.so_that}",
            user_story_id=story.id,
            scenarios=scenarios,
        ))

    coverage = []
    for story in contract_a.user_stories:
        for ac in story.acceptance_criteria:
            sc = [
                s for s in scenarios_por_story.get(story.id, [])
                if s.acceptance_criterion_id == ac.id
            ]
            if sc:
                coverage.append(CoverageMatrix(
                    user_story_id=story.id,
                    criterion_id=ac.id,
                    scenario_names=[s.name for s in sc],
                    coverage_type=[s.scenario_type for s in sc],
                    quality_characteristics_covered=list({s.quality_characteristic for s in sc}),
                ))

    all_sc = [s for f in features for s in f.scenarios]
    suite = GherkinTestSuite(
        pipeline_run_id=f"auto-{uuid.uuid4().hex[:8]}",
        agent_version="0.3.0-v3-iso25010",
        features=features,
        coverage_matrix=coverage,
        total_scenarios=len(all_sc),
        total_positive=sum(1 for s in all_sc if s.scenario_type == ScenarioType.POSITIVE),
        total_negative=sum(1 for s in all_sc if s.scenario_type == ScenarioType.NEGATIVE),
        total_boundary=sum(1 for s in all_sc if s.scenario_type == ScenarioType.BOUNDARY),
        coverage_by_characteristic=calcular_matriz_cobertura(all_sc),
    )
    print(f"   Features:             {len(suite.features)}")
    print(f"   Total escenarios:     {suite.total_scenarios}")
    print(f"   Criterios cubiertos:  {len(suite.coverage_matrix)}")
    return suite


# ============================================================
# REVISIÓN HUMANA — helpers de consola (de review_cli.py)
# ============================================================
def mostrar_escenario(scenario: GherkinScenario, idx: int, total: int):
    print()
    _sep("-")
    print(f" Escenario {idx + 1} de {total}")
    _sep("-")
    print(f"   Nombre:                  {scenario.name}")
    print(f"   Tipo:                    {scenario.scenario_type.value}")
    print(f"   Clasificación ISO 25010: {scenario.quality_characteristic.value}")
    print(f"   AC origen:               {scenario.acceptance_criterion_id}")
    print(f"   Tags:                    {', '.join(scenario.tags) if scenario.tags else '(sin tags)'}")
    print(f"   Pasos:")
    for step in scenario.steps:
        print(f"      {step.keyword:5s} {step.text}")


def menu_iso25010() -> QualityCharacteristic:
    print()
    print("   Selecciona la característica ISO 25010 correcta:")
    opciones = list(QualityCharacteristic)
    for i, qc in enumerate(opciones, 1):
        print(f"      {i}) {qc.value}")
    while True:
        elec = leer_input("   Número [1-8]: ", obligatorio=True)
        try:
            n = int(elec)
            if 1 <= n <= 8:
                return opciones[n - 1]
        except ValueError:
            pass
        print("   Opción inválida. Intenta de nuevo.")


def accion_reclasificar(scenario: GherkinScenario, reviewer: str, history: list[ReviewChange]) -> bool:
    nueva_qc = menu_iso25010()
    if nueva_qc == scenario.quality_characteristic:
        print("   La característica seleccionada es la misma — sin cambios.")
        return False
    nota = leer_input("   Razón del cambio (obligatoria): ", obligatorio=True)
    anterior = scenario.quality_characteristic.value
    scenario.quality_characteristic = nueva_qc
    scenario.tags = [t for t in scenario.tags if not t.lower().startswith("@iso-")]
    scenario.tags.append(f"@iso-{nueva_qc.value.replace('_', '-')}")
    history.append(ReviewChange(
        reviewer=reviewer,
        action="reclassified",
        notes=f"Escenario '{scenario.name}': {anterior} → {nueva_qc.value}. Razón: {nota}",
    ))
    print(f"   Reclasificado: {anterior} → {nueva_qc.value}")
    return True


def accion_comentar(scenario: GherkinScenario, reviewer: str, history: list[ReviewChange]):
    comentario = leer_input("   Comentario: ", obligatorio=True)
    history.append(ReviewChange(
        reviewer=reviewer,
        action="comment_added",
        notes=f"Escenario '{scenario.name}': {comentario}",
    ))
    print("   Comentario registrado.")


def accion_aceptar(scenario: GherkinScenario, reviewer: str, history: list[ReviewChange]):
    history.append(ReviewChange(
        reviewer=reviewer,
        action="accepted",
        notes=(
            f"Escenario '{scenario.name}': clasificación "
            f"'{scenario.quality_characteristic.value}' confirmada."
        ),
    ))
    print("   Aceptado.")


# ============================================================
# REVISIÓN HUMANA — loop escenario por escenario
# ============================================================
def revisar_escenarios(suite: GherkinTestSuite, reviewer: str, history: list[ReviewChange]) -> int:
    todos = [s for f in suite.features for s in f.scenarios]
    total = len(todos)
    cambios = 0

    _titulo(f"REVISIÓN ESCENARIO POR ESCENARIO ({total} escenarios)")
    print(" Acciones disponibles:")
    print("   [a] Aceptar la clasificación del LLM (sin cambios)")
    print("   [r] Reclasificar (elegir otra característica ISO 25010)")
    print("   [c] Agregar comentario (sin cambiar la clasificación)")
    print("   [s] Saltar (siguiente escenario, sin registrar acción)")
    print("   [q] Salir (el suite queda en pending_review)")

    for idx, scenario in enumerate(todos):
        mostrar_escenario(scenario, idx, total)
        while True:
            opc = leer_input("\n   Acción [a/r/c/s/q]: ", obligatorio=True).lower()
            if opc == "a":
                accion_aceptar(scenario, reviewer, history)
                break
            elif opc == "r":
                if accion_reclasificar(scenario, reviewer, history):
                    cambios += 1
                break
            elif opc == "c":
                accion_comentar(scenario, reviewer, history)
                break
            elif opc == "s":
                print("   Saltado.")
                break
            elif opc == "q":
                print(f"\n   Sesión interrumpida — revisados {idx} de {total}.")
                return cambios
            else:
                print("   Opción no válida. Usa: a, r, c, s, q.")
    return cambios


# ============================================================
# REVISIÓN HUMANA — recalcular matriz post-reclasificación
# ============================================================
def recalcular_matriz(suite: GherkinTestSuite):
    todos = [s for f in suite.features for s in f.scenarios]
    nueva = {qc.value: 0 for qc in QualityCharacteristic}
    for s in todos:
        nueva[s.quality_characteristic.value] += 1
    suite.coverage_by_characteristic = nueva
    for cm in suite.coverage_matrix:
        sc_ac = [s for s in todos if s.acceptance_criterion_id == cm.criterion_id]
        cm.quality_characteristics_covered = list({s.quality_characteristic for s in sc_ac})


def comparar_matrices(antes: dict[str, int], despues: dict[str, int]):
    _titulo("MATRIZ DE COBERTURA — ANTES VS DESPUÉS DE LA REVISIÓN")
    print(f"   {'Característica':<28} {'Antes':>8} {'Después':>10} {'Delta':>8}")
    print(f"   {'-' * 28} {'-' * 8} {'-' * 10} {'-' * 8}")
    for qc in QualityCharacteristic:
        a = antes.get(qc.value, 0)
        d = despues.get(qc.value, 0)
        delta = d - a
        delta_str = f"+{delta}" if delta > 0 else (str(delta) if delta < 0 else "-")
        print(f"   {qc.value:<28} {a:>8} {d:>10} {delta_str:>8}")


# ============================================================
# REVISIÓN HUMANA — decisión global
# ============================================================
def decision_global(suite: GherkinTestSuite, reviewer: str, history: list[ReviewChange]) -> ReviewStatus:
    _titulo("DECISIÓN GLOBAL SOBRE EL SUITE")
    print("   [a] APROBAR       — el suite avanza a la generación del acta")
    print("   [r] RECHAZAR      — el suite NO avanza, debe regenerarse")
    print("   [c] PEDIR CAMBIOS — aprobación condicional, versión sube")

    while True:
        opc = leer_input("\n   Decisión final [a/r/c]: ", obligatorio=True).lower()
        if opc in {"a", "r", "c"}:
            break
        print("   Opción no válida.")

    feedback = leer_input("   Comentario libre (opcional, Enter para omitir): ")

    if opc == "a":
        status = ReviewStatus.APPROVED
        suite.review.approved_by = reviewer
        suite.review.approved_at = datetime.now()
        action = "approved"
    elif opc == "r":
        status = ReviewStatus.REJECTED
        action = "rejected"
    else:
        status = ReviewStatus.NEEDS_CHANGES
        suite.review.version += 1
        action = "changes_requested"

    suite.review.review_status = status
    if feedback:
        suite.review.analyst_feedback = feedback

    history.append(ReviewChange(
        reviewer=reviewer,
        action=action,
        notes=feedback or f"Decisión final: {status.value}",
    ))
    return status


# ============================================================
# PERSISTENCIA — guardar Contract B revisado
# ============================================================
def guardar_contract_b_revisado(suite: GherkinTestSuite, output_dir: Path, timestamp: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"contract_b_auto_{timestamp}_reviewed.json"
    path.write_text(suite.model_dump_json(indent=2), encoding="utf-8")
    print(f"\n   Contract B revisado: {path.name}")
    return path


# ============================================================
# PIPELINE COMPLETO
# ============================================================
def pipeline(contract_a_path: str | None = None, output_dir: Path | None = None) -> tuple[Path, Path | None]:
    """Ejecuta el pipeline completo. Retorna (path_contract_b, path_acta | None)."""
    _titulo("PIPELINE UNIFICADO M1+M2 — Requerimientos + Generación + Revisión + Acta")

    # ---- FASE 0: REFINAMIENTO (M1) o carga de Contract A existente ----
    if contract_a_path is None:
        contract_a, _ = fase_refinamiento()
    else:
        contract_a = cargar_contract_a(contract_a_path)

    # ---- FASE 1: GENERACIÓN (M2) ----
    modelo, collection = inicializar_kb()

    print(f"\nPASO 3-6: Generando escenarios (RAG + EP/BVA/DT + ISO 25010)...")
    groq_client = Groq(api_key=GROQ_API_KEY)
    scenarios_por_story: dict[str, list[GherkinScenario]] = {}

    for story in contract_a.user_stories:
        print(f"\n   Historia {story.id}: {story.title}")
        scenarios_por_story[story.id] = []
        for ac in story.acceptance_criteria:
            print(f"      AC {ac.id}: {ac.description[:55]}...")
            patrones = buscar_patrones_similares(modelo, collection, ac, top_k=3)
            print(f"         RAG top-1: {patrones[0]['domain']} ({patrones[0]['similitud']:.2f})")
            system_prompt, user_message = construir_prompt(ac, story, patrones)
            raw = generar_con_groq(groq_client, system_prompt, user_message)
            try:
                escenarios = parsear_a_escenarios(raw, ac, story)
                scenarios_por_story[story.id].extend(escenarios)
                print(f"         Escenarios: {len(escenarios)}")
                for sc in escenarios:
                    h = next((t for t in sc.tags if t.lower() in ["@ep", "@bva", "@dt"]), "general")
                    print(f"            [{sc.scenario_type.value:12s}|{h:7s}|{sc.quality_characteristic.value}] {sc.name[:45]}")
            except (json.JSONDecodeError, ValidationError, KeyError, ValueError) as e:
                print(f"         Error en AC {ac.id}: {e}")

    suite = construir_contract_b(contract_a, scenarios_por_story)

    # ---- FASE 2: REVISIÓN HUMANA ----
    _titulo("FASE 2 — REVISIÓN HUMANA DEL ANALISTA DE QA")
    print(" El agente generó los escenarios. Ahora debes revisarlos y tomar una decisión.")

    reviewer = leer_input("\n Identificador del revisor (ej: ana.garcia): ", obligatorio=True)

    if suite.review.review_status == ReviewStatus.APPROVED:
        confirmar = leer_input(
            f"\n Atención: el suite YA está aprobado por {suite.review.approved_by}. "
            "¿Reabrir revisión? [s/n]: ",
            default="n",
        ).lower()
        if confirmar != "s":
            print(" Revisión cancelada.")

    matriz_original = deepcopy(suite.coverage_by_characteristic)
    history_nueva: list[ReviewChange] = []

    cambios = revisar_escenarios(suite, reviewer, history_nueva)

    if cambios > 0:
        recalcular_matriz(suite)
        comparar_matrices(matriz_original, suite.coverage_by_characteristic)
    else:
        print("\n No hubo reclasificaciones — la matriz se mantiene igual.")

    status = decision_global(suite, reviewer, history_nueva)
    suite.review.change_history.extend(history_nueva)

    # ---- FASE 3: PERSISTENCIA Y ACTA ----
    if output_dir is None:
        output_dir = Path(__file__).parent / "output"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    _titulo("FASE 3 — GUARDANDO RESULTADOS")
    contract_b_path = guardar_contract_b_revisado(suite, output_dir, timestamp)

    acta_path: Path | None = None
    if status == ReviewStatus.APPROVED:
        print("   Generando Acta de Aprobación HTML...")
        acta_path = guardar_acta(suite, contract_b_path)
        print(f"   Acta generada:       {acta_path.name}")
    else:
        print(f"   Estado del suite: {status.value} — el acta no se genera hasta que esté aprobado.")

    # Resumen
    _sep()
    print(f"   Estado final:        {suite.review.review_status.value}")
    print(f"   Revisor:             {suite.review.approved_by or '(no aprobado)'}")
    print(f"   Reclasificaciones:   {cambios}")
    print(f"   Acciones en historial: {len(suite.review.change_history)}")
    if acta_path:
        print()
        print("   Abre el acta en un navegador e imprime con Ctrl+P para obtener el PDF.")
    _sep()

    return contract_b_path, acta_path


# ============================================================
# EJECUCIÓN
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pipeline M1+M2: Requerimientos → Generación → Revisión humana → Acta"
    )
    parser.add_argument(
        "contract_a",
        nargs="?",
        default=None,
        help=(
            "(Opcional) Ruta a un Contract A JSON ya generado. "
            "Si se omite, se pedirá el requerimiento en texto libre y el agente M1 lo procesará."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directorio de salida (default: ./output)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else None
    pipeline(contract_a_path=args.contract_a, output_dir=output_dir)
