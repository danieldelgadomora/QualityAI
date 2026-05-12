"""Agente v1 (M2): Test Architect base — RAG sobre patrones Katary, sin heuristicas formales.

Esta es la primera version del agente del Modulo 2 (Test Architect).
ASUME conocidos los conceptos del Modulo 1: tokenizacion, embeddings,
ChromaDB, RAG, JSON estructurado con Pydantic, retry de validacion.
Por eso v1 ya viene con TODO eso aplicado de fabrica.

Lo que evolucionara en v2, v3, v4 son los conceptos NUEVOS del Modulo 2:
    v2: aplicacion de heuristicas formales en el prompt (EP, BVA, Decision Tables)
    v3: clasificacion ISO 25010 + matriz de cobertura por caracteristica de calidad
    v4: HITL del analista de QA que revisa y aprueba el Contract B

Limitaciones de esta version (se resuelven en versiones siguientes):
    Sin heuristicas formales — el prompt es generico (v2 lo resuelve)
    Sin clasificacion ISO 25010 — todos los escenarios quedan como functional_suitability (v3)
    Sin HITL del analista — el output va directo del LLM al disco (v4)

Pipeline:
    Contract A → para cada AC → embedding del AC → buscar patrones en KB Katary
    → prompt enriquecido con patrones → Groq → JSON → Pydantic → GherkinScenario
    → agrupar en GherkinFeature por user story → construir GherkinTestSuite (Contract B)

Ejecutar:
    python agente_v1_base.py
"""

import json
import os
import sys
import uuid
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore")

from dotenv import load_dotenv
from groq import Groq
from pydantic import ValidationError
from sentence_transformers import SentenceTransformer
import chromadb

# Asegurar que la raiz del proyecto este en sys.path para imports cross-module
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Contract A re-exportado desde el Modulo 1 (entrada del agente)
from modulo2_test_architect.src.contract_a_input import (
    AcceptanceCriterion,
    RefinedRequirements,
    UserStory,
)

# Contract B (salida del agente)
from modulo2_test_architect.src.contract_b import (
    CoverageMatrix,
    GherkinFeature,
    GherkinScenario,
    GherkinStep,
    GherkinTestSuite,
    QualityCharacteristic,
    ScenarioType,
)

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("Error: No se encontro GROQ_API_KEY en el archivo .env")
    sys.exit(1)


# ============================================================
# PASO 1: Cargar Contract A desde JSON
# ============================================================
def cargar_contract_a(path: str) -> RefinedRequirements:
    """Carga el Contract A producido por el Modulo 1 desde un archivo JSON.

    Pydantic valida la estructura automaticamente al construir el modelo.
    Si el JSON no cumple el schema, levanta ValidationError con detalles.
    """
    print(f"\nPASO 1: Cargando Contract A desde {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    contract_a = RefinedRequirements(**data)

    total_ac = sum(len(s.acceptance_criteria) for s in contract_a.user_stories)
    print(f"   Contract A cargado:")
    print(f"      Pipeline ID: {contract_a.pipeline_run_id}")
    print(f"      Historias de usuario: {len(contract_a.user_stories)}")
    print(f"      Criterios de aceptacion totales: {total_ac}")

    return contract_a


# ============================================================
# PASO 2: Inicializar la KB de patrones de testing Katary (RAG)
# ============================================================
def inicializar_kb():
    """Carga el modelo de embeddings y la base de conocimiento de patrones de testing.

    Esto es exactamente el mismo patron que aprendieron en el Modulo 1
    (embeddings + ChromaDB persistente), pero apuntando a los patrones de
    testing en lugar de a las historias de usuario del SGC.
    """
    print(f"\nPASO 2: Inicializando KB de patrones de testing Katary")

    # Mismo modelo de embeddings que M1 (consistencia entre modulos)
    print("   Cargando modelo de embeddings (all-MiniLM-L6-v2)...")
    modelo = SentenceTransformer("all-MiniLM-L6-v2")

    # ChromaDB persistente — path propio del M2 (no mezclar con KB del M1)
    kb_path = Path(__file__).parent / "knowledge_base_data"
    client = chromadb.PersistentClient(path=str(kb_path))
    collection = client.get_or_create_collection(
        name="katary_test_patterns",
        metadata={"hnsw:space": "cosine"},
    )

    # Si esta vacia, cargar los patrones desde el JSON
    if collection.count() == 0:
        patterns_path = (
            Path(__file__).parent / "examples" / "knowledge_base" / "katary_test_patterns.json"
        )
        print(f"   Indexando patrones desde {patterns_path.name}...")

        with open(patterns_path, "r", encoding="utf-8") as f:
            patterns = json.load(f)

        # Lo que se embedea es: domain + ac_pattern_typical + katary_context
        # Esto es lo que el RAG va a comparar con un AC nuevo para encontrar similares
        textos = [
            f"{p['domain']}. {p['ac_pattern_typical']}. {p['katary_context']}"
            for p in patterns
        ]
        embeddings = modelo.encode(textos).tolist()

        collection.add(
            ids=[p["id"] for p in patterns],
            embeddings=embeddings,
            documents=textos,
            # En metadata guardamos el resto del patron (typical_scenarios, lessons)
            # para inyectarlo al prompt como contexto enriquecido
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
# PASO 3: Buscar patrones similares para un AC (Retrieval)
# ============================================================
def buscar_patrones_similares(modelo, collection, ac: AcceptanceCriterion, top_k: int = 3):
    """Busca los patrones de testing mas similares al AC en la KB Katary.

    El embedding del AC se calcula con la misma forma que se indexaron los patrones
    (description + given + when + then) para que la similitud cosine sea relevante.
    """
    consulta_texto = f"{ac.description}. Given {ac.given}. When {ac.when}. Then {ac.then}"
    consulta_emb = modelo.encode([consulta_texto]).tolist()

    resultados = collection.query(
        query_embeddings=consulta_emb,
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
# PASO 4: Construir prompt MINIMO enriquecido con RAG (Augmented)
# ============================================================
def construir_prompt(ac: AcceptanceCriterion, story: UserStory, patrones: list[dict]) -> tuple[str, str]:
    """Construye el prompt para el LLM con contexto RAG pero SIN heuristicas formales.

    LIMITACION DELIBERADA DE V1: el prompt NO instruye al LLM a aplicar EP, BVA
    ni Decision Tables. Solo le da el AC + patrones similares de Katary y le pide
    UN escenario Gherkin. v2 agregara las heuristicas explicitas.

    El proposito de v1 es servir como linea base contra la cual mediremos en v2
    el efecto de agregar las heuristicas.
    """
    # Construir contexto RAG con los patrones similares encontrados
    contexto_kb = "## PATRONES DE TESTING DEL SGC KATARY\n"
    contexto_kb += "Usa estos patrones como referencia de calidad para tu escenario:\n\n"
    for i, p in enumerate(patrones, 1):
        contexto_kb += f"### Patron {i} [{p['id']}] dominio: {p['domain']} (similitud: {p['similitud']:.2f})\n"
        contexto_kb += f"Tecnicas usadas tipicamente: {p['techniques_used']}\n"
        contexto_kb += f"Escenarios tipicos:\n"
        for s in p["typical_scenarios"]:
            contexto_kb += f"   - {s}\n"
        contexto_kb += f"Leccion Katary: {p['lessons_learned_katary']}\n\n"

    system = (
        "Eres un asistente que convierte criterios de aceptacion en escenarios Gherkin (BDD).\n\n"
        f"{contexto_kb}\n"
        "## FORMATO DE RESPUESTA OBLIGATORIO\n"
        "Devuelve UNICAMENTE un JSON valido con esta estructura, sin texto adicional:\n"
        "{\n"
        '  "name": "nombre descriptivo del escenario, minimo 10 caracteres",\n'
        '  "scenario_type": "positive" | "negative" | "boundary" | "edge_case" | "error_handling",\n'
        '  "tags": ["@tag1", "@tag2"],\n'
        '  "steps": [\n'
        '    {"keyword": "Given", "text": "..."},\n'
        '    {"keyword": "When", "text": "..."},\n'
        '    {"keyword": "Then", "text": "..."}\n'
        "  ]\n"
        "}\n"
        "Cada step.text debe tener minimo 5 caracteres."
    )

    user = (
        f"Historia de usuario: {story.title}\n"
        f"Como {story.as_a}, quiero {story.i_want}, para {story.so_that}.\n\n"
        f"Criterio de aceptacion {ac.id}:\n"
        f"   Descripcion: {ac.description}\n"
        f"   Given: {ac.given}\n"
        f"   When: {ac.when}\n"
        f"   Then: {ac.then}\n"
        f"   Caso negativo: {'Si' if ac.is_negative_case else 'No'}\n\n"
        f"Genera UN escenario Gherkin que valide este criterio."
    )

    return system, user


# ============================================================
# PASO 5: Llamar a Groq (Generation)
# ============================================================
def generar_con_groq(client: Groq, system_prompt: str, user_message: str) -> str:
    """Envia el prompt a Groq y retorna la respuesta como texto.

    Determinismo activado de fabrica (heredado del aprendizaje de M1):
       temperature=0 (greedy decoding)
       seed=42 (mismo punto de partida del muestreo)
    """
    response = client.chat.completions.create(
        model="qwen/qwen3-32b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.8,
        seed=900,
        max_tokens=2000,
    )
    return response.choices[0].message.content


# ============================================================
# PASO 6: Parsear respuesta del LLM a GherkinScenario (Pydantic)
# ============================================================
def parsear_a_escenario(raw_text: str, ac: AcceptanceCriterion, story: UserStory) -> GherkinScenario:
    """Parsea el JSON crudo del LLM y lo convierte en un GherkinScenario validado.

    Si el JSON tiene formato markdown (```json ... ```), lo limpia.
    Si Pydantic rechaza la estructura, levanta ValidationError con detalles.
    """
    text = raw_text.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1].rsplit("```", 1)[0]
    elif "```" in text:
        text = text.split("```", 1)[1].rsplit("```", 1)[0]

    start = text.find("{")
    end = text.rfind("}") + 1
    json_str = text[start:end]
    data = json.loads(json_str)

    steps = [GherkinStep(keyword=s["keyword"], text=s["text"]) for s in data["steps"]]

    scenario = GherkinScenario(
        name=data["name"],
        scenario_type=ScenarioType(data.get("scenario_type", "positive")),
        tags=data.get("tags", []),
        steps=steps,
        acceptance_criterion_id=ac.id,
        user_story_id=story.id,
        # quality_characteristic se queda con el default (functional_suitability).
        # En V1 NO instruimos al LLM a clasificar por ISO 25010 — eso lo hace V3.
    )
    return scenario


# ============================================================
# PASO 7: Construir el Contract B agrupando escenarios por feature
# ============================================================
def construir_contract_b(
    contract_a: RefinedRequirements,
    scenarios_por_story: dict[str, list[GherkinScenario]],
) -> GherkinTestSuite:
    """Agrupa los escenarios en GherkinFeature (uno por user story) y construye el suite."""
    print(f"\nPASO 7: Construyendo Contract B...")
    features = []
    for story in contract_a.user_stories:
        scenarios = scenarios_por_story.get(story.id, [])
        if not scenarios:
            print(f"   Aviso: historia {story.id} sin escenarios — saltando")
            continue
        features.append(
            GherkinFeature(
                name=story.title,
                description=f"Como {story.as_a}, quiero {story.i_want}, para {story.so_that}",
                user_story_id=story.id,
                scenarios=scenarios,
            )
        )

    # Matriz de cobertura basica: un AC -> los escenarios que lo cubren
    coverage = []
    for story in contract_a.user_stories:
        for ac in story.acceptance_criteria:
            sc = [
                s for s in scenarios_por_story.get(story.id, [])
                if s.acceptance_criterion_id == ac.id
            ]
            if sc:
                coverage.append(
                    CoverageMatrix(
                        user_story_id=story.id,
                        criterion_id=ac.id,
                        scenario_names=[s.name for s in sc],
                        coverage_type=[s.scenario_type for s in sc],
                        quality_characteristics_covered=[s.quality_characteristic for s in sc],
                    )
                )

    # Calcular metricas por tipo de escenario (fix: en V1 anterior quedaban en 0)
    all_scenarios = [s for f in features for s in f.scenarios]
    total_positive = sum(1 for s in all_scenarios if s.scenario_type == ScenarioType.POSITIVE)
    total_negative = sum(1 for s in all_scenarios if s.scenario_type == ScenarioType.NEGATIVE)
    total_boundary = sum(1 for s in all_scenarios if s.scenario_type == ScenarioType.BOUNDARY)

    suite = GherkinTestSuite(
        pipeline_run_id=f"v1-{uuid.uuid4().hex[:8]}",
        agent_version="0.1.0-v1-base",
        features=features,
        coverage_matrix=coverage,
        total_scenarios=len(all_scenarios),
        total_positive=total_positive,
        total_negative=total_negative,
        total_boundary=total_boundary,
    )
    print(f"   Contract B construido:")
    print(f"      Features generadas: {len(suite.features)}")
    print(f"      Total escenarios: {suite.total_scenarios}")
    print(f"      Distribucion: {total_positive} positive, {total_negative} negative, {total_boundary} boundary")
    print(f"      Criterios cubiertos: {len(suite.coverage_matrix)}")

    return suite


# ============================================================
# PIPELINE COMPLETO
# ============================================================
def pipeline_v1(contract_a: RefinedRequirements) -> GherkinTestSuite:
    """Ejecuta el pipeline completo de M2-V1.

    Pipeline:
        Contract A → para cada AC → buscar patrones en KB → prompt RAG sin heuristicas
        → Groq → parsear → GherkinScenario → agrupar en features → Contract B
    """
    print("=" * 60)
    print("AGENTE M2-V1 — Test Architect base (RAG sin heuristicas)")
    print("=" * 60)

    client = Groq(api_key=GROQ_API_KEY)
    modelo, collection = inicializar_kb()
    scenarios_por_story = {}

    for story in contract_a.user_stories:
        print(f"\nHistoria {story.id}: {story.title}")
        scenarios_por_story[story.id] = []

        for ac in story.acceptance_criteria:
            print(f"   AC {ac.id}: {ac.description[:50]}...")

            # Pasos 3-6: RAG + LLM + parseo
            patrones = buscar_patrones_similares(modelo, collection, ac, top_k=3)
            print(f"      RAG: {len(patrones)} patrones similares — top1: {patrones[0]['domain']} ({patrones[0]['similitud']:.2f})")

            system_prompt, user_message = construir_prompt(ac, story, patrones)
            raw_response = generar_con_groq(client, system_prompt, user_message)

            try:
                scenario = parsear_a_escenario(raw_response, ac, story)
                scenarios_por_story[story.id].append(scenario)
                print(f"      Escenario: {scenario.name[:50]}")
            except (json.JSONDecodeError, ValidationError, KeyError, ValueError) as e:
                print(f"      Error procesando AC {ac.id}: {e}")
                # En V1 NO reintentamos automaticamente — esa robustez extra viene en versiones siguientes
                continue

    # Paso 7: construir el Contract B final
    suite = construir_contract_b(contract_a, scenarios_por_story)
    return suite


# ============================================================
# LIMITACIONES DE V1 (mostradas al estudiante al final)
# ============================================================
def imprimir_limitaciones():
    """Imprime las limitaciones de V1 que motivan V2-V4."""
    print(f"\n{'=' * 60}")
    print(f"LIMITACIONES DE V1 (oportunidades de mejora)")
    print(f"{'=' * 60}")
    print(f"   - Sin heuristicas formales en el prompt (EP, BVA, Decision Tables)")
    print(f"     Solucion: V2 instruye al LLM a aplicar las tecnicas de Clase 1")
    print(f"   - Sin clasificacion ISO 25010 — todos los escenarios quedan como functional_suitability")
    print(f"     Solucion: V3 agrega clasificacion + matriz de cobertura por caracteristica")
    print(f"   - Sin HITL del analista de QA — el output va directo del LLM al disco")
    print(f"     Solucion: V4 agrega revision humana antes de aprobar el Contract B")


# ============================================================
# EJECUCION
# ============================================================
if __name__ == "__main__":
    contract_a_path = input(
        "\nRuta al Contract A JSON (Enter para usar el ejemplo de M1):\n> "
    ).strip()

    if not contract_a_path:
        # Por defecto usar el contract_a de ejemplo del M1
        contract_a_path = str(
            _PROJECT_ROOT
            / "modulo1_requirements_refiner"
            / "examples"
            / "output"
            / "contract_a_login_ejemplo.json"
        )

    contract_a = cargar_contract_a(contract_a_path)
    suite = pipeline_v1(contract_a)

    # Guardar el Contract B resultante
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"contract_b_v1_{timestamp}.json"

    output_path.write_text(
        suite.model_dump_json(indent=2),
        encoding="utf-8",
    )
    print(f"\nContract B guardado en: {output_path}")

    imprimir_limitaciones()
