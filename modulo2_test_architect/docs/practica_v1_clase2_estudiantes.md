# Práctica V1 — Construye + Experimenta + Audita

> **Curso:** Calidad de Software y Pruebas Automatizadas
> **Módulo:** 2 — Test Architect Agent
> **Clase:** 2
> **Tiempo:** 15 minutos en parejas
> **Modalidad:** parejas con su propio computador y `GROQ_API_KEY` configurada (la misma del Módulo 1)

---

## Contexto

Acaban de ver en presencial el agente **M2-V1 (Test Architect base)**. Ya saben qué hace: recibe un Contract A del Módulo 1 y produce un Contract B con escenarios Gherkin (BDD) usando RAG sobre la base de conocimiento de patrones de testing del SGC Katary.

En esta práctica van a **aportar conocimiento propio** a la base, **experimentar con el comportamiento del agente**, y **observar cómo sus cambios afectan la salida**. La idea no es solo verlo correr — es ponerle las manos al agente y entenderlo desde adentro.

---

## Las 3 acciones que van a hacer

### Acción 1 — Construir un patrón propio para la KB Katary

Abran el archivo `examples/knowledge_base/katary_test_patterns.json`. Vean los 10 patrones que ya están y la estructura común.

**Su tarea:** agregar **un patrón nuevo** que cubra un dominio que no esté presente. Pueden inventar el dominio (ej: `chat_messaging`, `geolocation`, `shopping_cart`, `appointment_booking`, `health_records`, `online_learning`, `loyalty_program`...) o uno técnico que falta (ej: `email_validation`, `cache_management`, `webhooks`).

El patrón debe tener TODOS los campos del schema:

| Campo | Qué debe contener |
|---|---|
| `id` | Siguiente número disponible (ej: `PTN-011`) |
| `domain` | Nombre técnico en inglés, snake_case |
| `katary_context` | Oración que describa el contexto Katary |
| `ac_pattern_typical` | Qué tipo de criterio de aceptación encaja en este patrón |
| `techniques_used` | Lista: alguna combinación de `EP`, `BVA`, `Decision Tables` |
| `typical_scenarios` | Mínimo 4 escenarios típicos a probar |
| `lessons_learned_katary` | Lección que ustedes inventan, basada en lo que creen que pasaría en producción |

**Importante:** después de agregar el patrón, **borren la carpeta `knowledge_base_data/`** para que la KB se reindexe con su nuevo patrón en la siguiente ejecución.

---

### Acción 2 — Experimentar con un hiperparámetro del agente


Cada pareja escoge **UN** experimento de los siguientes y lo ejecuta:

#### Experimento A — Cambiar `top_k`

En la función `buscar_patrones_similares()` del archivo `agente_v1_base.py`, cambien `top_k=3` por `top_k=1` (solo el más similar) o `top_k=5` (más diversidad). Ejecuten V1 sobre el mismo Contract A. ¿Cómo cambia el contexto que el LLM recibe?

#### Experimento B — Cambiar `temperature`

En la función `generar_con_groq()`, cambien `temperature=0.0` por `temperature=0.7`. Ejecuten V1 dos veces sobre el mismo Contract A. ¿Las salidas son ahora más distintas entre sí?

#### Experimento C — Cambiar `seed`

Cambien `seed=42` por `seed=999`. Ejecuten V1 sobre el mismo Contract A. ¿La estructura de la salida cambió? ¿La redacción cambió?

**Anoten en una línea qué observaron** en su experimento.

---

### Acción 3 — Diseñar un AC propio que invoque su patrón + verificar


Construyan un Contract A pequeño con **una user story** y **un criterio de aceptación** relacionado con el dominio del patrón que crearon en la Acción 1.

> *Ejemplo:* si crearon un patrón sobre `shopping_cart`, escriban un AC sobre "el sistema permite agregar productos al carrito y calcular el total".

Pueden usar como plantilla cualquier `contract_a_*.json` del Módulo 1 — solo modifiquen el contenido para que apunte a su dominio.

Ejecuten V1 sobre este Contract A nuevo. **Verifiquen tres cosas:**

1. **¿El RAG encontró el patrón que ustedes crearon?** Revisen la línea de log que dice `RAG: 3 patrones similares — top1: ...`. Idealmente su patrón debería aparecer en el top-1 o top-2.
2. **¿El escenario Gherkin generado refleja la "lección aprendida"** que escribieron en su patrón?
3. **¿El LLM "usó" la información de su patrón** o ignoró el contexto y generó algo genérico?

---

## Entregable final

Al terminar cada pareja prepara un reporte breve con:

| Sección | Contenido |
|---|---|
| **1. Su patrón nuevo** | Copien el JSON del patrón que agregaron a la KB |
| **2. El experimento que hicieron** | Indiquen cuál (A, B o C) y qué observaron en una frase |
| **3. El AC que diseñaron** | Resumen de si el RAG encontró su patrón y si el escenario generado lo reflejó |
| **4. Una lección personal** | ¿Qué entendieron de V1 con esta práctica que NO sabían antes? |

---

## Comandos útiles

**Ejecutar V1:**
```bash
python agente_v1_base.py
```

**Borrar la KB indexada para que se reindexe** (después de modificar el JSON de patrones):
```bash
# En PowerShell (Windows)
Remove-Item -Recurse -Force knowledge_base_data

# En bash (Linux/Mac)
rm -rf knowledge_base_data
```

**Activar el venv si no está activo:**
```bash
# En PowerShell (Windows)
.\venv\Scripts\Activate.ps1

# En bash (Linux/Mac)
source venv/bin/activate
```

---

## Recordatorio

Esta práctica vale para que ustedes **interioricen V1 a fondo** antes de pasar a V2. La calidad de su reporte depende de tres cosas: (a) que su patrón tenga sustancia, no solo campos llenos por llenar; (b) que su observación del experimento sea específica, no vaga; (c) que su lección personal sea genuina — qué entienden ahora que antes no.

¡Manos al código!
