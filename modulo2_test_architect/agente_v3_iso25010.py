"""Agente v3 (M2): Test Architect con clasificacion ISO/IEC 25010.

Esta es la tercera version del agente del Modulo 2. Mismo agente que v2
estructuralmente — mismo flujo, misma KB, mismo determinismo, mismas
heuristicas EP/BVA/DT.
LO UNICO que cambia respecto a v2 es:
    1. El prompt agrega un cuarto bloque de instrucciones: clasificar cada
       escenario con UNA caracteristica de calidad ISO/IEC 25010.
    2. El parser lee `quality_characteristic` del JSON y lo asigna al
       GherkinScenario (en v2 quedaba en el default functional_suitability).
    3. Al cerrar el Contract B se calcula la matriz de cobertura por
       caracteristica (un dict {functional_suitability: 22, security: 4, ...})
       y se guarda en suite.coverage_by_characteristic.
    4. La matriz se imprime al final de la corrida — el "tablero" para
       responder al cliente "¿cuantos escenarios cubren seguridad?".

¿Por que separar v2 de v3?
    Para que los estudiantes vean en vivo la diferencia entre un agente que
    AMPLIFICA (v2 genera mas escenarios disciplinados) y un agente que
    AMPLIFICA + CLASIFICA (v3 organiza esos escenarios en una taxonomia
    estandar de calidad). Mismo codigo, mismo modelo, misma KB — solo
    cambia la INSTRUCCION al LLM y el calculo de la matriz.
    Esa es la leccion central: el prompt no solo guia QUE genera el LLM,
    tambien guia COMO etiqueta lo que genera.

Cambios concretos respecto a v2:
    1. SYSTEM_PROMPT enriquecido con un cuarto bloque de instrucciones
       (clasificacion ISO 25010 por escenario).
    2. Formato JSON esperado: cada escenario ahora trae un campo
       `quality_characteristic` obligatorio.
    3. Parser lee quality_characteristic y lo aplica al GherkinScenario.
    4. Funcion nueva calcular_matriz_cobertura() que agrupa por caracteristica.
    5. construir_contract_b() rellena suite.coverage_by_characteristic y
       actualiza quality_characteristics_covered en cada CoverageMatrix.
    6. agent_version cambia a "0.3.0-v3-iso25010".
    7. La salida imprime la matriz de cobertura para uso del stakeholder.

Limitaciones que aun tiene v3 (se resuelven en versiones siguientes):
    Sin HITL del analista — el output sigue yendo directo al disco (v4)
    Confianza ciega en la clasificacion del LLM — la matriz puede mentir si
    el LLM clasifica mal. Esa es exactamente la motivacion de v4: un humano
    debe validar quality_characteristic de cada escenario antes de creer en
    los numeros que reporta la matriz.

Pipeline:
    Contract A → para cada AC → embedding del AC → buscar patrones en KB Katary
    → prompt enriquecido CON HEURISTICAS + CLASIFICACION ISO 25010
    → Groq → JSON con LISTA de escenarios CON quality_characteristic
    → Pydantic → multiples GherkinScenario CLASIFICADOS por AC
    → calcular matriz de cobertura por caracteristica
    → construir GherkinTestSuite con matriz incluida

Ejecutar:
    python agente_v3_iso25010.py
"""

import json
import os
import sys
import uuid
import warnings
from collections import Counter
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

    Mismo patron que v1/v2 — la KB no cambia entre versiones del agente.
    Lo que evoluciona V1->V4 es como el agente USA la KB, no la KB en si.
    """
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
# PASO 3: Buscar patrones similares para un AC (Retrieval)
# ============================================================
def buscar_patrones_similares(modelo, collection, ac: AcceptanceCriterion, top_k: int = 3):
    """Busca los patrones de testing mas similares al AC en la KB Katary.

    Identico a v1/v2. La parte de Retrieval del RAG no cambia entre versiones.
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
# PASO 4: Construir prompt enriquecido con RAG + Heuristicas + ISO 25010
# ============================================================
def construir_prompt(ac: AcceptanceCriterion, story: UserStory, patrones: list[dict]) -> tuple[str, str]:
    """Construye el prompt para el LLM con RAG + heuristicas + clasificacion ISO 25010.

    DIFERENCIA CLAVE RESPECTO A V2:
    Se agrega un CUARTO bloque al prompt instruyendo al LLM a clasificar cada
    escenario con UNA caracteristica de calidad ISO/IEC 25010. El formato JSON
    esperado tambien se extiende: cada escenario debe traer el campo
    `quality_characteristic`. Todo lo demas (EP, BVA, DT, lista de escenarios)
    se hereda intacto de v2.
    """
    # Contexto RAG (igual que v1/v2)
    contexto_kb = "## PATRONES DE TESTING DEL SGC KATARY\n"
    contexto_kb += "Usa estos patrones como referencia de calidad para tus escenarios:\n\n"
    for i, p in enumerate(patrones, 1):
        contexto_kb += f"### Patron {i} [{p['id']}] dominio: {p['domain']} (similitud: {p['similitud']:.2f})\n"
        contexto_kb += f"Tecnicas usadas tipicamente: {p['techniques_used']}\n"
        contexto_kb += f"Escenarios tipicos:\n"
        for s in p["typical_scenarios"]:
            contexto_kb += f"   - {s}\n"
        contexto_kb += f"Leccion Katary: {p['lessons_learned_katary']}\n\n"

    # Heredado de V2: instrucciones operacionales de testing disciplinado
    instrucciones_heuristicas = (
        "## INSTRUCCIONES DE TESTING DISCIPLINADO (OBLIGATORIAS)\n"
        "\n"
        "Para el criterio de aceptacion recibido, aplica las siguientes tecnicas\n"
        "de caja negra de manera explicita:\n"
        "\n"
        "1. EQUIVALENCE PARTITIONING (EP):\n"
        "   - Identifica las clases equivalentes validas e invalidas del AC.\n"
        "   - Genera UN escenario por cada clase identificada (no uno solo).\n"
        "   - Si el AC trae multiples test_data_examples, cada uno suele\n"
        "     representar una clase distinta — genera un escenario por cada uno.\n"
        "\n"
        "2. BOUNDARY VALUE ANALYSIS (BVA):\n"
        "   - Si el AC menciona un rango numerico (ej: edad entre 18 y 99),\n"
        "     genera 4 escenarios adicionales con: limite inferior, justo\n"
        "     debajo del inferior, limite superior, justo encima del superior.\n"
        "   - Si el AC menciona longitudes de string (ej: password de 8 a 64\n"
        "     caracteres), aplica BVA-2 sobre la longitud.\n"
        "   - Si el AC tiene boundary_values listados explicitamente, usalos.\n"
        "\n"
        "3. DECISION TABLES (DT):\n"
        "   - Si el AC tiene multiples condiciones que se combinan, genera UN\n"
        "     escenario por cada combinacion relevante segun las reglas.\n"
        "\n"
        "## RESULTADO ESPERADO (cantidad)\n"
        "   - Minimo 1 escenario positivo (si el AC describe un caso valido)\n"
        "   - Minimo 1 escenario por cada clase invalida identificada\n"
        "   - Si aplica BVA: 4 escenarios adicionales para los bordes\n"
        "   - Si aplica DT: 1 escenario por cada regla de la tabla\n"
        "\n"
        "NO te conformes con UN escenario por AC. Aplica disciplina formal.\n"
        "Si el AC es pobre en informacion (sin rangos, sin reglas, sin ejemplos),\n"
        "genera al menos los escenarios que SI puedas justificar — no inventes\n"
        "datos no especificados en el AC.\n"
    )

    # NUEVO en V3: instruccion de clasificacion ISO/IEC 25010
    instrucciones_iso25010 = (
        "## CLASIFICACION ISO/IEC 25010 (OBLIGATORIA)\n"
        "\n"
        "Por cada escenario que generes, asigna OBLIGATORIAMENTE el campo\n"
        "`quality_characteristic` con UNA de estas 8 categorias estandar:\n"
        "\n"
        "   - functional_suitability  (logica de negocio, validaciones, reglas, calculos)\n"
        "   - performance_efficiency  (tiempos de respuesta, consumo de recursos, carga concurrente)\n"
        "   - security                (autenticacion, autorizacion, bloqueo de cuentas, proteccion de credenciales,\n"
        "                              cifrado, prevencion de inyeccion, datos sensibles)\n"
        "   - usability               (mensajes de error claros, accesibilidad, navegacion, lectores de pantalla,\n"
        "                              consistencia de la UI)\n"
        "   - reliability             (recuperacion de fallas, manejo de errores, tolerancia a interrupciones,\n"
        "                              consistencia de datos tras fallas)\n"
        "   - compatibility           (interoperabilidad con otros sistemas, formatos de archivo, navegadores,\n"
        "                              versiones de SO)\n"
        "   - maintainability         (rara vez aplica a escenarios BDD funcionales)\n"
        "   - portability             (rara vez aplica a escenarios BDD funcionales)\n"
        "\n"
        "REGLAS PARA DECIDIR:\n"
        "   - Si el escenario PRUEBA una validacion de entrada o una regla de negocio:\n"
        "     functional_suitability.\n"
        "   - Si el escenario PRUEBA bloqueo de cuenta tras N intentos, control de acceso\n"
        "     por rol, proteccion de contraseñas o prevencion de inyeccion:\n"
        "     security.\n"
        "   - Si el escenario PRUEBA tiempo de respuesta, concurrencia o consumo de recursos:\n"
        "     performance_efficiency.\n"
        "   - Si el escenario PRUEBA mensaje de error claro al usuario, accesibilidad,\n"
        "     navegacion intuitiva o consistencia de la UI:\n"
        "     usability.\n"
        "   - Si el escenario PRUEBA recuperacion tras caida, manejo de timeout o\n"
        "     consistencia post-falla:\n"
        "     reliability.\n"
        "   - Si el escenario PRUEBA comportamiento en distintos navegadores, SO,\n"
        "     formatos de archivo o protocolos:\n"
        "     compatibility.\n"
        "\n"
        "NO asignes la categoria 'por defecto'. Decide caso por caso, leyendo\n"
        "que es lo que de verdad esta probando ese escenario. Si dudas entre\n"
        "dos, escoge la mas especifica (ej: bloqueo tras N intentos es security,\n"
        "no functional_suitability, aunque sea 'una regla').\n"
    )

    system = (
        "Eres un Test Architect que convierte criterios de aceptacion en\n"
        "escenarios Gherkin (BDD) aplicando tecnicas de caja negra disciplinadas\n"
        "y clasificandolos segun ISO/IEC 25010.\n\n"
        f"{contexto_kb}\n"
        f"{instrucciones_heuristicas}\n"
        f"{instrucciones_iso25010}\n"
        "## FORMATO DE RESPUESTA OBLIGATORIO\n"
        "Devuelve UNICAMENTE un JSON valido con esta estructura (LISTA de escenarios):\n"
        "{\n"
        '  "scenarios": [\n'
        "    {\n"
        '      "name": "nombre descriptivo del escenario, minimo 10 caracteres",\n'
        '      "scenario_type": "positive" | "negative" | "boundary" | "edge_case" | "error_handling",\n'
        '      "quality_characteristic": "functional_suitability" | "performance_efficiency" | "security" |\n'
        '                                "usability" | "reliability" | "compatibility" |\n'
        '                                "maintainability" | "portability",\n'
        '      "tags": ["@tag1", "@tag2"],\n'
        '      "heuristic_applied": "EP" | "BVA" | "DT" | "general",\n'
        '      "steps": [\n'
        '        {"keyword": "Given", "text": "..."},\n'
        '        {"keyword": "When", "text": "..."},\n'
        '        {"keyword": "Then", "text": "..."}\n'
        "      ]\n"
        "    },\n"
        "    // ... mas escenarios segun heuristicas aplicadas\n"
        "  ]\n"
        "}\n"
        "\n"
        "Cada step.text debe tener minimo 5 caracteres.\n"
        "Cada escenario debe declarar:\n"
        "   - que heuristica aplico (EP, BVA, DT, general)\n"
        "   - que caracteristica ISO 25010 valida (uno de los 8 valores)\n"
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
        f"Genera la LISTA de escenarios Gherkin que validen este criterio,\n"
        f"aplicando EP, BVA y/o Decision Tables segun corresponda, y CLASIFICA\n"
        f"cada escenario con su caracteristica ISO/IEC 25010."
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

    max_tokens sube a 2500 porque V3 agrega un campo mas por escenario
    (quality_characteristic) — pequeño aumento por seguridad.
    """
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
# PASO 6: Parsear respuesta del LLM a GherkinScenario (Pydantic)
# ============================================================
def parsear_a_escenarios(raw_text: str, ac: AcceptanceCriterion, story: UserStory) -> list[GherkinScenario]:
    """Parsea el JSON crudo del LLM y lo convierte en una LISTA de GherkinScenario validados.

    DIFERENCIA RESPECTO A V2:
    Ahora cada escenario del JSON trae quality_characteristic. El parser lo
    lee, valida que pertenezca al enum, y lo asigna al GherkinScenario. Si el
    LLM omite el campo o pone un valor invalido, el escenario se queda con
    el default functional_suitability (degradacion grace).
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

    scenarios_data = data.get("scenarios", [])
    if not scenarios_data:
        raise ValueError(f"LLM no devolvio escenarios para AC {ac.id}")

    valid_qc_values = {qc.value for qc in QualityCharacteristic}
    scenarios = []
    for scenario_data in scenarios_data:
        steps = [GherkinStep(keyword=s["keyword"], text=s["text"]) for s in scenario_data["steps"]]

        # Heuristica como tag (heredado de V2)
        tags = scenario_data.get("tags", [])
        heuristica = scenario_data.get("heuristic_applied", "general")
        if heuristica != "general" and f"@{heuristica.lower()}" not in [t.lower() for t in tags]:
            tags.append(f"@{heuristica.lower()}")

        # NUEVO en V3: leer y validar quality_characteristic del LLM
        qc_raw = scenario_data.get("quality_characteristic", "functional_suitability")
        if qc_raw not in valid_qc_values:
            print(
                f"      Aviso: LLM devolvio quality_characteristic invalida "
                f"'{qc_raw}' — usando functional_suitability como fallback"
            )
            qc_raw = "functional_suitability"
        quality_characteristic = QualityCharacteristic(qc_raw)

        # NUEVO en V3: tag adicional por caracteristica para trazabilidad rapida
        # (ej: @iso-security, @iso-performance) — facilita filtrar en runners BDD
        iso_tag = f"@iso-{quality_characteristic.value.replace('_', '-')}"
        if iso_tag not in [t.lower() for t in tags]:
            tags.append(iso_tag)

        scenarios.append(GherkinScenario(
            name=scenario_data["name"],
            scenario_type=ScenarioType(scenario_data.get("scenario_type", "positive")),
            quality_characteristic=quality_characteristic,
            tags=tags,
            steps=steps,
            acceptance_criterion_id=ac.id,
            user_story_id=story.id,
        ))
    return scenarios


# ============================================================
# PASO 7: Calcular matriz de cobertura por caracteristica ISO 25010 (V3)
# ============================================================
def calcular_matriz_cobertura(escenarios: list[GherkinScenario]) -> dict[str, int]:
    """Cuenta escenarios por caracteristica ISO 25010.

    Ejemplo de salida:
        {
            "functional_suitability": 22,
            "security": 4,
            "usability": 2,
            "performance_efficiency": 0,
            "reliability": 0,
            "compatibility": 0,
            "maintainability": 0,
            "portability": 0,
        }

    Esto es el "tablero" que V3 entrega al stakeholder. Para que el cliente
    pregunte "cuantos escenarios cubren seguridad?" y se responda con un
    numero — no con un parrafo.

    Limitacion conocida: depende de la clasificacion del LLM. Si el LLM
    clasifico mal, esta matriz miente. La validacion humana llega en V4.
    """
    matriz = {qc.value: 0 for qc in QualityCharacteristic}
    contador = Counter(e.quality_characteristic.value for e in escenarios)
    matriz.update(contador)
    return matriz


# ============================================================
# PASO 8: Construir el Contract B agrupando escenarios por feature
# ============================================================
def construir_contract_b(
    contract_a: RefinedRequirements,
    scenarios_por_story: dict[str, list[GherkinScenario]],
) -> GherkinTestSuite:
    """Agrupa los escenarios en GherkinFeature y construye el suite.

    DIFERENCIA RESPECTO A V2:
    Ahora rellena suite.coverage_by_characteristic con la matriz global y
    cada CoverageMatrix.quality_characteristics_covered con las caracteristicas
    cubiertas por los escenarios de cada AC.
    """
    print(f"\nPASO 8: Construyendo Contract B con matriz de cobertura ISO 25010...")
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

    # Matriz de cobertura por AC (heredado de V2 — ahora con quality_characteristics_covered poblado)
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
                        # V3: lista UNICA de caracteristicas cubiertas por este AC
                        quality_characteristics_covered=list(
                            {s.quality_characteristic for s in sc}
                        ),
                    )
                )

    # Metricas por tipo de escenario (heredado de V2)
    all_scenarios = [s for f in features for s in f.scenarios]
    total_positive = sum(1 for s in all_scenarios if s.scenario_type == ScenarioType.POSITIVE)
    total_negative = sum(1 for s in all_scenarios if s.scenario_type == ScenarioType.NEGATIVE)
    total_boundary = sum(1 for s in all_scenarios if s.scenario_type == ScenarioType.BOUNDARY)

    # NUEVO en V3: matriz global de cobertura ISO 25010
    matriz_iso = calcular_matriz_cobertura(all_scenarios)

    suite = GherkinTestSuite(
        pipeline_run_id=f"v3-{uuid.uuid4().hex[:8]}",
        agent_version="0.3.0-v3-iso25010",
        features=features,
        coverage_matrix=coverage,
        total_scenarios=len(all_scenarios),
        total_positive=total_positive,
        total_negative=total_negative,
        total_boundary=total_boundary,
        coverage_by_characteristic=matriz_iso,
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
def pipeline_v3(contract_a: RefinedRequirements) -> GherkinTestSuite:
    """Ejecuta el pipeline completo de M2-V3.

    Pipeline:
        Contract A → para cada AC → buscar patrones en KB → prompt RAG CON
        heuristicas + ISO 25010 → Groq → parsear LISTA escenarios CLASIFICADOS
        → multiples GherkinScenario por AC → calcular matriz de cobertura
        → Contract B con matriz incluida.
    """
    print("=" * 70)
    print("AGENTE M2-V3 — Test Architect con clasificacion ISO/IEC 25010")
    print("(RAG + EP + BVA + DT + ISO 25010)")
    print("=" * 70)

    client = Groq(api_key=GROQ_API_KEY)
    modelo, collection = inicializar_kb()
    scenarios_por_story = {}

    for story in contract_a.user_stories:
        print(f"\nHistoria {story.id}: {story.title}")
        scenarios_por_story[story.id] = []

        for ac in story.acceptance_criteria:
            print(f"   AC {ac.id}: {ac.description[:50]}...")

            patrones = buscar_patrones_similares(modelo, collection, ac, top_k=3)
            print(f"      RAG: {len(patrones)} patrones similares — top1: {patrones[0]['domain']} ({patrones[0]['similitud']:.2f})")

            system_prompt, user_message = construir_prompt(ac, story, patrones)
            raw_response = generar_con_groq(client, system_prompt, user_message)

            try:
                escenarios_generados = parsear_a_escenarios(raw_response, ac, story)
                scenarios_por_story[story.id].extend(escenarios_generados)
                print(f"      Escenarios generados: {len(escenarios_generados)}")
                for sc in escenarios_generados:
                    heuristic_tag = next(
                        (t for t in sc.tags if t.lower() in ['@ep', '@bva', '@dt']),
                        'general',
                    )
                    print(
                        f"         [{sc.scenario_type.value} | {heuristic_tag} | "
                        f"{sc.quality_characteristic.value}] {sc.name[:50]}"
                    )
            except (json.JSONDecodeError, ValidationError, KeyError, ValueError) as e:
                print(f"      Error procesando AC {ac.id}: {e}")
                continue

    suite = construir_contract_b(contract_a, scenarios_por_story)
    return suite


# ============================================================
# IMPRIMIR MATRIZ DE COBERTURA ISO 25010 (output ejecutivo)
# ============================================================
def imprimir_matriz_cobertura(suite: GherkinTestSuite):
    """Imprime la matriz de cobertura ISO 25010 como tablero ejecutivo.

    Esta es la salida que V3 ofrece al stakeholder. Tres columnas:
        Caracteristica | Conteo | Estado
    El estado es un indicador semantico:
        - "no cubierto" si conteo == 0
        - "ligero"  si 1 <= conteo < 5
        - "robusto" si conteo >= 5
    """
    print(f"\n{'=' * 70}")
    print(f"MATRIZ DE COBERTURA ISO/IEC 25010")
    print(f"{'=' * 70}")
    print(f"   {'Caracteristica':<28} {'Escenarios':>10}   {'Estado':<12}")
    print(f"   {'-' * 28} {'-' * 10}   {'-' * 12}")

    matriz = suite.coverage_by_characteristic
    # Imprimir en el orden del enum para consistencia visual entre corridas
    for qc in QualityCharacteristic:
        conteo = matriz.get(qc.value, 0)
        if conteo == 0:
            estado = "no cubierto"
        elif conteo < 5:
            estado = "ligero"
        else:
            estado = "robusto"
        print(f"   {qc.value:<28} {conteo:>10}   {estado:<12}")
    print(f"   {'-' * 28} {'-' * 10}   {'-' * 12}")
    print(f"   {'TOTAL':<28} {suite.total_scenarios:>10}")
    print(f"{'=' * 70}")


# ============================================================
# LIMITACIONES DE V3
# ============================================================
def imprimir_limitaciones():
    """Imprime las limitaciones de V3 que motivan V4."""
    print(f"\n{'=' * 70}")
    print(f"LIMITACIONES DE V3 (oportunidades de mejora)")
    print(f"{'=' * 70}")
    print(f"   - Limitacion sutil heredada de V2: V3 AMPLIFICA Y CLASIFICA lo que el AC")
    print(f"     tiene, NO INVENTA. Si el AC es pobre, los huecos en la matriz")
    print(f"     son resultado del input, no de V3.")
    print(f"   - Confianza ciega en la clasificacion del LLM:")
    print(f"     La matriz de cobertura puede MENTIR si el LLM clasifica mal un escenario")
    print(f"     (ej: un escenario de seguridad etiquetado como functional_suitability).")
    print(f"     Esto produce DOS errores opuestos:")
    print(f"        a) un hueco real (caracteristica realmente descuidada) se ve igual que")
    print(f"        b) una mala clasificacion (cubierto pero etiquetado como otra cosa).")
    print(f"     Solucion: V4 agrega revision humana del analista — un humano valida cada")
    print(f"     escenario antes de creer en los numeros que reporta esta matriz.")


# ============================================================
# EJECUCION
# ============================================================
if __name__ == "__main__":
    contract_a_path = input(
        "\nRuta al Contract A JSON (Enter para usar el ejemplo de M1):\n> "
    ).strip()

    if not contract_a_path:
        contract_a_path = str(
            _PROJECT_ROOT
            / "modulo1_requirements_refiner"
            / "examples"
            / "output"
            / "contract_a_login_ejemplo.json"
        )

    contract_a = cargar_contract_a(contract_a_path)
    suite = pipeline_v3(contract_a)

    # Guardar el Contract B resultante
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"contract_b_v3_{timestamp}.json"

    output_path.write_text(
        suite.model_dump_json(indent=2),
        encoding="utf-8",
    )
    print(f"\nContract B guardado en: {output_path}")

    # NUEVO en V3: tablero de cobertura por caracteristica ISO 25010
    imprimir_matriz_cobertura(suite)
    imprimir_limitaciones()
