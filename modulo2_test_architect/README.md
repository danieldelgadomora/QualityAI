# QualityAI · Módulo 2 — Test Architect Agent

> Pipeline de 4 agentes de IA que transforman criterios de aceptación (Contract A) en escenarios de prueba Gherkin BDD disciplinados, clasificados por ISO/IEC 25010 y firmados por un analista humano.

**Curso:** Calidad de Software y Pruebas Automatizadas
**Institución:** Universidad de Nariño
**Empresa:** Katary Software (CMMI-DEV L3)

---

## ¿Qué hace este módulo?

Recibe un **Contract A** (la salida del [Módulo 1 — Requirements Refiner](https://github.com/Juan-construsoft/qualityai-modulo1)) y produce un **Contract B**: un suite Gherkin BDD listo para que el Módulo 3 (Code Generator) lo convierta en código de pruebas automatizadas.

El módulo evoluciona en 4 versiones, cada una agregando **un único concepto nuevo** sobre la anterior:

| Versión | Capacidad agregada | Archivo |
|---|---|---|
| **V1** | Línea base — RAG sobre KB Katary, Pydantic, determinismo, 1 escenario por AC | `agente_v1_base.py` |
| **V2** | Heurísticas formales en el prompt — Equivalence Partitioning, Boundary Value Analysis, Decision Tables | `agente_v2_heuristicas.py` |
| **V3** | Clasificación ISO/IEC 25010 + matriz de cobertura por característica de calidad | `agente_v3_iso25010.py` |
| **V4** | Human-in-the-Loop — el analista de QA revisa, reclasifica y firma cada Contract B | `review_cli.py` |

---

## Estructura del módulo

```
modulo2_test_architect/
├── agente_v1_base.py            # V1 — Línea base (RAG + Pydantic + determinismo)
├── agente_v2_heuristicas.py     # V2 — Prompt con EP + BVA + Decision Tables
├── agente_v3_iso25010.py        # V3 — Clasificación ISO 25010 + matriz cobertura
├── review_cli.py                # V4 — CLI de revisión humana (HITL)
│
├── src/
│   ├── contract_a_input.py      # Re-export del schema Contract A desde M1
│   └── contract_b.py            # Schema Contract B (Pydantic v2)
│
├── serializers/
│   └── gherkin_writer.py        # Serialización a archivos .feature
│
├── examples/
│   └── knowledge_base/
│       └── katary_test_patterns.json   # KB de 10 patrones de testing Katary
│
├── docs/
│   ├── practica_ep_clase1_estudiantes.md
│   ├── practica_bva_clase1_estudiantes.md
│   ├── practica_decision_tables_clase1_estudiantes.md
│   ├── practica_v1_clase2_estudiantes.md
│   ├── practica_v2_clase2_estudiantes.md
│   ├── practica_v3_clase3_estudiantes.md
│   ├── practica_v4_clase4_estudiantes.md
│   └── guia_estudio_prework_m2.md
│
├── notebooks/
│   └── 02_prework_fundamentos_istqb.ipynb
│
├── images/
│   └── m2_v1_test_architect_flow.svg
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## Requisitos

- **Python 3.10+**
- Una **GROQ_API_KEY** (free tier disponible en https://console.groq.com/)
- El **Módulo 1** clonado al lado de este módulo (necesario para el re-export del Contract A): https://github.com/Juan-construsoft/qualityai-modulo1

La estructura recomendada en tu computador:

```
QualityAI/
├── modulo1_requirements_refiner/   # Repositorio del Módulo 1
└── modulo2_test_architect/         # ESTE repositorio
```

---

## Instalación

### 1. Clonar el repositorio

```powershell
# PowerShell (Windows) o bash (Linux/Mac)
cd ruta/a/QualityAI
git clone https://github.com/Juan-construsoft/qualityai-modulo2.git modulo2_test_architect
cd modulo2_test_architect
```

### 2. Crear entorno virtual

```powershell
# PowerShell (Windows)
python -m venv venv
.\venv\Scripts\Activate.ps1

# bash (Linux/Mac)
python -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar la API key

```bash
cp .env.example .env
# Editar .env y reemplazar 'tu_api_key_aqui' con tu GROQ_API_KEY real
```

---

## Cómo ejecutar cada versión

### V1 — Línea base

```bash
python agente_v1_base.py
```

Cuando pida la ruta del Contract A, presiona Enter para usar el ejemplo del Módulo 1 (login). Genera 1 escenario Gherkin por criterio de aceptación.

### V2 — Heurísticas formales

```bash
python agente_v2_heuristicas.py
```

Aplica EP, BVA y Decision Tables. Genera múltiples escenarios disciplinados por criterio.

### V3 — Clasificación ISO 25010

```bash
python agente_v3_iso25010.py
```

Cada escenario se clasifica con una característica ISO/IEC 25010. Al final imprime la matriz de cobertura como tablero ejecutivo.

### V4 — Revisión humana

```bash
python review_cli.py
```

Cargas un Contract B previamente generado por V3 y lo revisas escenario por escenario. Reclasificas, comentas y firmas. La salida queda en un archivo `*_reviewed.json` con `change_history` completo.

---

## El pipeline completo

```
Contract A (de M1)
    ↓
[V1] → Contract B v1 (1 escenario por AC, sin clasificar)
    ↓
[V2] → Contract B v2 (múltiples escenarios disciplinados)
    ↓
[V3] → Contract B v3 (clasificado ISO 25010, con matriz de cobertura)
    ↓
[V4] → Contract B v3_reviewed (firmado por analista, change_history completo)
    ↓
(Módulo 3 — Code Generator)
```

Cada versión hereda completo a la anterior. V3 incluye TODO lo de V1 y V2; V4 opera sobre el output de V3.

---

## Material complementario

### Prácticas de aula (handouts de estudiantes)

| Clase | Tema | Archivo |
|---|---|---|
| Clase 1 | Equivalence Partitioning | `docs/practica_ep_clase1_estudiantes.md` |
| Clase 1 | Boundary Value Analysis | `docs/practica_bva_clase1_estudiantes.md` |
| Clase 1 | Decision Tables | `docs/practica_decision_tables_clase1_estudiantes.md` |
| Clase 2 | Construye + Experimenta + Audita (V1) | `docs/practica_v1_clase2_estudiantes.md` |
| Clase 2 | Ablation Study del Prompt (V2) | `docs/practica_v2_clase2_estudiantes.md` |
| Clase 3 | Auditoría humana de la matriz (V3) | `docs/practica_v3_clase3_estudiantes.md` |
| Clase 4 | Calibración inter-revisores (V4) | `docs/practica_v4_clase4_estudiantes.md` |

### Prework

- `docs/guia_estudio_prework_m2.md` — Guía breve de los 6 fundamentos ISTQB que el módulo asume conocidos.
- `notebooks/02_prework_fundamentos_istqb.ipynb` — Quiz de validación (10 preguntas).

---

## Frase de cierre del módulo

> *V1 dio el agente. V2 dio disciplina. V3 dio lenguaje. V4 dio firma.*
>
> *V4 no garantiza que la matriz sea correcta — V4 garantiza que la matriz sea defensible.*
>
> *Trazabilidad > perfección. CMMI-DEV L3 te exige procesos auditables, no humanos infalibles.*

---

## Licencia y créditos

Material académico desarrollado para el curso de Calidad de Software y Pruebas Automatizadas, Universidad de Nariño 2026, en colaboración con Katary Software.

Stack: Groq + Llama 3.3 70B Versatile · sentence-transformers · ChromaDB · Pydantic v2.
