"""
============================================================
TALLER: EVOLUCIÓN DEL AGENTE — Sección 1 de 4
============================================================
VERSIÓN: v1 — RAG Básico (texto libre)
CONCEPTO: El valor de la base de conocimiento en la generación

En esta sección van a:
1. Ejecutar el pipeline RAG con un requerimiento ambiguo
2. Ver la diferencia entre generar CON y SIN base de conocimiento
3. Intentar extraer información estructurada de la salida
4. Descubrir por qué el texto libre es un problema

Ejecutar desde la carpeta modulo1_requirements_refiner:
    python taller_evolucion/taller_seccion1_rag.py
============================================================
"""

import json
import os
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

# Configurar paths
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import SentenceTransformer
import chromadb

load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("Error: No se encontro GROQ_API_KEY en el archivo .env")
    sys.exit(1)

# ============================================================
# REQUERIMIENTO DE PRUEBA — ESTE MISMO SE USA EN LAS 4 SECCIONES
# ============================================================
REQUERIMIENTO = "El sistema debe gestionar usuarios de forma segura y eficiente, permitiendo el registro y autenticacion de usuarios"

print("=" * 70)
print("TALLER: EVOLUCION DEL AGENTE")
print("Seccion 1 de 4: RAG Basico (texto libre)")
print("=" * 70)
print(f"\nRequerimiento de prueba:")
print(f'  "{REQUERIMIENTO}"')
print(f"\nEste mismo requerimiento se usara en las 4 secciones.")
input("\nPresione Enter para iniciar...")


# ============================================================
# PASO 1: Inicializar componentes
# ============================================================
print(f"\n{'─' * 70}")
print("PASO 1: Inicializando modelo de embeddings y base de conocimiento")
print(f"{'─' * 70}")

print("\nCargando modelo de embeddings (all-MiniLM-L6-v2)...")
modelo = SentenceTransformer("all-MiniLM-L6-v2")
print("  Modelo cargado")

kb_path = BASE_DIR / "knowledge_base_data"
client = chromadb.PersistentClient(path=str(kb_path))
collection = client.get_or_create_collection(
    name="katary_sgc",
    metadata={"hnsw:space": "cosine"},
)

if collection.count() == 0:
    print("\nCargando historias del SGC de Katary...")
    stories_path = BASE_DIR / "examples" / "knowledge_base" / "katary_stories.json"
    with open(stories_path, "r", encoding="utf-8") as f:
        stories = json.load(f)

    textos = [s["texto"] for s in stories]
    embeddings = modelo.encode(textos).tolist()
    collection.add(
        ids=[s["id"] for s in stories],
        embeddings=embeddings,
        documents=textos,
        metadatas=[{"dominio": s.get("dominio", "general"), "criterios": s.get("criterios", "")} for s in stories],
    )
    print(f"  {collection.count()} historias indexadas")
else:
    print(f"\nBase de conocimiento existente: {collection.count()} historias")

input("\nPresione Enter para buscar historias similares...")


# ============================================================
# PASO 2: Buscar historias similares (Retrieval)
# ============================================================
print(f"\n{'─' * 70}")
print("PASO 2: Buscando historias similares en ChromaDB (Retrieval)")
print(f"{'─' * 70}")
print(f"\nEl requerimiento se convierte a embedding y se buscan las 3 mas cercanas.\n")

query_emb = modelo.encode([REQUERIMIENTO]).tolist()
resultados = collection.query(
    query_embeddings=query_emb,
    n_results=3,
    include=["documents", "metadatas", "distances"],
)

historias = []
for i in range(len(resultados["ids"][0])):
    sim = 1 - resultados["distances"][0][i]
    h = {
        "id": resultados["ids"][0][i],
        "texto": resultados["documents"][0][i],
        "criterios": resultados["metadatas"][0][i].get("criterios", ""),
        "dominio": resultados["metadatas"][0][i].get("dominio", ""),
        "similitud": sim,
    }
    historias.append(h)
    emoji = "ALTA" if sim > 0.5 else "MEDIA" if sim > 0.3 else "BAJA"
    print(f"  [{h['id']}] Similitud: {sim:.3f} ({emoji}) — Dominio: {h['dominio']}")

input("\nPresione Enter para construir el prompt RAG...")


# ============================================================
# PASO 3: Construir prompt enriquecido (Augmented)
# ============================================================
print(f"\n{'─' * 70}")
print("PASO 3: Construyendo prompt enriquecido (Augmented)")
print(f"{'─' * 70}")

contexto_kb = "## HISTORIAS DE REFERENCIA DEL SGC DE KATARY\n"
contexto_kb += "Usa estas historias como modelo de calidad y profundidad:\n\n"
for i, h in enumerate(historias, 1):
    contexto_kb += f"### Referencia {i} [{h['id']}] (similitud: {h['similitud']:.2f})\n"
    contexto_kb += f"**Historia:** {h['texto']}\n"
    contexto_kb += f"**Criterios:** {h['criterios']}\n\n"

system_prompt = f"""Eres un Analista de Requerimientos Senior de Katary Software,
empresa colombiana con 19 anos de experiencia y certificacion CMMI-DEV Nivel 3.

Tu trabajo es transformar requerimientos ambiguos en historias de usuario profesionales
con criterios de aceptacion Given/When/Then verificables.

REGLAS:
1. Formato: "Como [rol], quiero [accion], para que [beneficio]"
2. Criterios de aceptacion en formato Given/When/Then con validaciones especificas
3. Incluir validaciones de datos (longitudes, formatos, rangos)
4. Incluir tiempos de respuesta esperados
5. Incluir manejo de errores y casos limite
6. Incluir al menos un caso negativo por cada caso positivo
7. Detectar y resolver ambiguedades con valores concretos

{contexto_kb}"""

user_message = f"""Transforma el siguiente requerimiento en historias de usuario
con el mismo nivel de calidad y detalle que las historias de referencia.

REQUERIMIENTO:
{REQUERIMIENTO}

Genera las historias de usuario completas con criterios Given/When/Then detallados."""

print(f"\nEl prompt tiene 2 partes:")
print(f"  System prompt: {len(system_prompt)} caracteres (reglas + historias de referencia)")
print(f"  User message:  {len(user_message)} caracteres (el requerimiento)")
print(f"  Total:         {len(system_prompt) + len(user_message)} caracteres")

input("\nPresione Enter para generar CON RAG...")


# ============================================================
# PASO 4: Generar CON RAG
# ============================================================
print(f"\n{'─' * 70}")
print("PASO 4: Generando historias CON RAG (con base de conocimiento)")
print(f"{'─' * 70}")
print("\nEnviando a Groq (llama-3.3-70b-versatile)...")

groq_client = Groq(api_key=GROQ_API_KEY)
respuesta_rag = groq_client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ],
    temperature=0.3,
    max_tokens=3000,
)

resultado_con_rag = respuesta_rag.choices[0].message.content
print(f"  Respuesta recibida ({respuesta_rag.usage.total_tokens} tokens)")

print(f"\n{'=' * 70}")
print("RESULTADO CON RAG")
print(f"{'=' * 70}")
print(resultado_con_rag)

input("\nPresione Enter para generar SIN RAG y comparar...")


# ============================================================
# PASO 5: Generar SIN RAG (para comparar)
# ============================================================
print(f"\n{'─' * 70}")
print("PASO 5: Generando historias SIN RAG (sin base de conocimiento)")
print(f"{'─' * 70}")
print("\nMismo requerimiento, pero sin historias de referencia...\n")

respuesta_sin = groq_client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "system", "content": "Eres un Analista de Requerimientos. Responde en espanol."},
        {"role": "user", "content": f"Transforma este requerimiento en historias de usuario con criterios Given/When/Then.\n\nREQUERIMIENTO: {REQUERIMIENTO}"},
    ],
    temperature=0.3,
    max_tokens=3000,
)

resultado_sin_rag = respuesta_sin.choices[0].message.content

print(f"{'=' * 70}")
print("RESULTADO SIN RAG")
print(f"{'=' * 70}")
print(resultado_sin_rag)


# ============================================================
# PASO 6: Comparacion y analisis
# ============================================================
print(f"\n\n{'=' * 70}")
print("COMPARACION")
print(f"{'=' * 70}")
print(f"  Sin RAG: {len(resultado_sin_rag)} caracteres")
print(f"  Con RAG: {len(resultado_con_rag)} caracteres")
print(f"  Historias de referencia usadas: {len(historias)}")


# ============================================================
# PASO 7: Descubrir la limitacion
# ============================================================
print(f"\n\n{'=' * 70}")
print("EJERCICIO: Intenten extraer datos de la salida")
print(f"{'=' * 70}")
print(f"""
La salida del agente es TEXTO LIBRE. Intenten responder estas preguntas
mirando el resultado CON RAG:

  1. Cuantas historias de usuario genero? (cuenten manualmente)
  2. Cual es el "Given" del primer criterio de aceptacion?
     (busquenlo en el texto... donde empieza? donde termina?)
  3. Cuantos criterios negativos hay?
  4. La palabra "seguro" del requerimiento, como la resolvio?

Ahora imaginen que otro programa (el Agente 2) necesita leer esta salida
automaticamente para generar casos de prueba. Como lo haria?
  - No puede buscar por lineas porque el formato cambia cada vez
  - No puede buscar por palabras clave porque el LLM las redacta diferente
  - No puede validar que la salida este completa

CONCLUSION: El texto libre NO SIRVE para un pipeline automatizado.
Necesitamos estructura. Eso es lo que resuelve la Seccion 2.
""")

print(f"\n{'=' * 70}")
print("PREGUNTAS DE REFLEXION — Seccion 1")
print(f"{'=' * 70}")
print("""
Respondan en grupo:

  1. Que diferencias concretas encontraron entre la salida CON RAG
     y SIN RAG? Mencionen al menos 3.

  2. Si ejecutan este mismo script otra vez, la salida sera identica?
     Por que si o por que no? Que implicaciones tiene eso?

  3. Un programa automatico podria parsear esta salida de forma
     confiable? Que pasaria si el formato cambia entre ejecuciones?

Cuando hayan respondido, ejecuten la Seccion 2:
  python taller_evolucion/taller_seccion2_json.py
""")
