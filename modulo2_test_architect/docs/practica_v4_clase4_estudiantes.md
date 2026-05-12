# Práctica V4 — Calibración inter-revisores en HITL

> **Curso:** Calidad de Software y Pruebas Automatizadas
> **Módulo:** 2 — Test Architect Agent
> **Clase:** 4
> **Tiempo:** 25 minutos individuales/parejas + 10 minutos de puesta en común
> **Modalidad:** primero individual (cada estudiante revisa solo), después en parejas (compararse), después juntos (proponer)

---

## Contexto

Acaban de ver en presencial cómo V4 incorpora al analista humano dentro del pipeline (HITL — Human-in-the-Loop). Saben en teoría que `review_cli.py` les permite revisar cada escenario del Contract B, reclasificar las que el LLM clasificó mal, y dejar todo trazable en el `change_history`.

Hoy van a **ser ese analista humano** y descubrir algo incómodo y muy importante: **el humano también puede ser inconsistente**. Y esa inconsistencia, sin un proceso para gestionarla, es el siguiente eslabón débil del pipeline después del LLM.

V4 no resuelve la verdad de la matriz. V4 la hace **trazable y defensible** — y eso es lo que CMMI-DEV L3 te exige. Esta práctica les hace vivirlo en carne propia.

---

## Las 3 acciones que van a hacer

### Acción 1 — Revisar el Contract B individualmente

> **Tiempo:** 10 minutos
> **Modalidad: cada estudiante en su propio computador, NO se hablen entre ustedes durante esta acción.**

Ejecuten `review_cli.py` sobre el Contract B V3 que tienen en `output/`:

```bash
python review_cli.py
```

Identifíquense con su nombre (formato `nombre.apellido`) y seleccionen el `contract_b_v3_*.json` más reciente (o el que les indique el docente).

Recorran los **20 escenarios uno por uno**. Por cada escenario decidan:

- `[a]` aceptar la clasificación del LLM
- `[r]` reclasificar — escojan la característica ISO 25010 que ustedes consideren correcta y dejen su justificación
- `[c]` solo comentar
- `[s]` saltar

Al final, escojan `[a]` aprobar el suite y dejen un comentario libre opcional sobre el suite completo.

**Importante:** apliquen su criterio personal, sin consultar a su pareja. Si dudan en un escenario, escojan lo que crean. La inconsistencia entre criterios es justo lo que vamos a estudiar después.

Cuando termine, anoten:
- Cuántos escenarios reclasificaron
- Cuál es su matriz `coverage_by_characteristic` final
- El path del archivo `_reviewed.json` que generaron

> *Tip:* recuerden la regla del tutorial — si el `Then` verifica el TEXTO del mensaje al usuario, hay componente de usability. Si verifica una regla de negocio, es functional_suitability. Si verifica protección contra acceso indebido, es security.

---

### Acción 2 — Calibración inter-revisores

> **Tiempo:** 8 minutos
> **Modalidad: ahora SÍ en pareja. Junten sus computadores.**

Abran los DOS archivos `*_reviewed.json` (uno por cada quien). Comparen:

| Métrica | Estudiante A | Estudiante B | ¿Coinciden? |
|---|---|---|---|
| Total reclasificaciones | | | |
| `coverage_by_characteristic.functional_suitability` | | | |
| `coverage_by_characteristic.security` | | | |
| `coverage_by_characteristic.usability` | | | |
| Otros (especificar) | | | |

Después, recorran el `change_history` de cada uno y construyan esta segunda tabla — **solo los escenarios donde sus decisiones difirieron**:

| Escenario (nombre corto) | Decisión A | Decisión B | ¿Quién tiene "razón"? |
|---|---|---|---|
| | | | |

> *Pista para la última columna:* en muchos casos NO HAY una respuesta universalmente correcta. Anoten *"ambos defendibles con criterio diferente"* cuando aplique.

**Reflexionen** dos minutos en pareja:

- ¿Cuántos escenarios revisaron diferente?
- ¿Sus razones escritas en las notas son lo suficientemente claras para que un tercero entienda por qué cada quien escogió lo que escogió?
- Si **ustedes mismos** difieren tanto, ¿qué pasaría con un equipo de 5 analistas en Katary revisando el mismo Contract B?

---

### Acción 3 — Diseñar un protocolo de calibración

> **Tiempo:** 7 minutos
> **Modalidad: en pareja, juntos.**

Como pareja, **propongan un mecanismo concreto** que Katary podría implementar para reducir la inconsistencia entre revisores. Aterricen al menos **dos elementos** del siguiente menú (o inventen los suyos):

- Una **lista de reglas operativas** (3-5 reglas) que todos los analistas de Katary deben aplicar al revisar un Contract B. Ejemplo: *"Si el `Then` verifica texto literal entre comillas, hay componente de usability."*
- Un **set de escenarios canónicos** etiquetados como ground-truth. Cualquier analista nuevo se calibra contra ellos antes de revisar producción.
- Un **protocolo de doble revisión** para escenarios borderline (ambos analistas tienen que estar de acuerdo).
- Un **arbitraje de líder técnico** cuando dos revisores no coinciden.
- Un **registro de decisiones precedentes** que sirva como referencia.

Escriban su propuesta en su reporte — concreta, no abstracta. Si proponen "reglas", escriban las reglas. Si proponen "ground-truth", den un ejemplo.

> *Reflexión:* el problema NO se resuelve con un agente más listo. Se resuelve con un proceso de QA más maduro.

---

## Entregable final

Al cerrar los 25 minutos, cada pareja prepara un reporte breve con:

| Sección | Contenido |
|---|---|
| **1. Mi revisión individual** | Cada estudiante anota: # reclasificaciones, matriz final, archivo generado (Acción 1) |
| **2. Tabla de discrepancias** | La tabla de "decisiones diferentes" entre pareja (Acción 2) |
| **3. Protocolo de calibración propuesto** | Mecanismo concreto, mínimo dos elementos aterrizados (Acción 3) |
| **4. Lección personal** | ¿Cuál es la diferencia real entre HITL y "tener un humano que revisa"? Conecten con CMMI L3 si lo conocen. |

---

## Comandos útiles

**Ejecutar review_cli.py:**
```bash
python review_cli.py
```

**Activar el venv si no está activo:**
```bash
# PowerShell (Windows)
.\venv\Scripts\Activate.ps1

# bash (Linux/Mac)
source venv/bin/activate
```

**Ver el `change_history` rápido:**
Abran el `*_reviewed.json` y busquen `"change_history"` con `Ctrl+F`. Cada entrada tiene `timestamp`, `reviewer`, `action`, `notes`.

**Comparar dos JSON en pareja:**
Si tienen VS Code instalado, pueden usar:
```bash
code --diff archivo_A_reviewed.json archivo_B_reviewed.json
```

---

## Recordatorio

Esta práctica las pone **en el rol del analista humano dentro del pipeline** — no como espectadoras, como protagonistas. La calidad de su reporte depende de tres cosas:

1. Que su **revisión individual sea genuina** — apliquen su criterio, no copien al compañero ni intenten ser "perfectas". La inconsistencia es el dato.
2. Que su **tabla de discrepancias sea honesta** — anoten todas las diferencias, no las disimulen.
3. Que su **protocolo de calibración sea aterrizado** — que un analista nuevo de Katary pueda leerlo y aplicarlo al día siguiente, no que sea filosofía abstracta.

**Pregunten al docente cualquier duda durante los 25 minutos. La puesta en común al final es para compartir hallazgos y propuestas, no para resolver dudas básicas.**

¡A revisar como humanos!
