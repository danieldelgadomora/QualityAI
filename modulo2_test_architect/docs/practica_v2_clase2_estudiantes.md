# Práctica V2 — Ablation Study del Prompt

> **Curso:** Calidad de Software y Pruebas Automatizadas
> **Módulo:** 2 — Test Architect Agent
> **Clase:** 2
> **Tiempo:** 25 minutos individuales en parejas + 10 minutos de puesta en común
> **Modalidad:** parejas con su propio computador, `GROQ_API_KEY` configurada y venv activo

---

## Contexto

Acaban de ver en presencial cómo V2 enriquece el prompt de V1 con instrucciones operacionales para EP, BVA y Decision Tables. Saben en teoría que V2 produce más escenarios y mejor distribución.

Ahora van a **medir el efecto en datos reales** y **modificar el prompt** para ver cada heurística en acción. Esta es la práctica más cercana a lo que un ingeniero de calidad asistido por IA hace en producción: experimentar con el prompt, medir el efecto, ajustar.

---

## Las 3 acciones que van a hacer

### Acción 1 — Comparar V1 vs V2 sobre el mismo Contract A

> **Tiempo:** 5 minutos

Ya tienen su `contract_b_v1_*.json` de la práctica anterior. Ejecuten ahora V2 sobre el mismo Contract A:

```bash
python agente_v2_heuristicas.py
```

Apreten Enter para usar el Contract A de ejemplo del M1 (el de login).

Una vez generado el `contract_b_v2_*.json`, abran ambos archivos y construyan esta tabla comparativa:

| Métrica | V1 | V2 | Diferencia |
|---|---|---|---|
| Total escenarios | | | |
| Positive | | | |
| Negative | | | |
| Boundary | | | |
| Tags `@ep` | | | |
| Tags `@bva` | | | |
| Tags `@dt` | | | |

**Tip:** las métricas `total_positive`, `total_negative`, `total_boundary` están al final del JSON. Para contar tags, usen búsqueda de texto (`Ctrl+F`) en cada archivo.

---

### Acción 2 — Deshabilitar UNA heurística del prompt

> **Tiempo:** 10 minutos

Cada pareja escoge **UNA** heurística para deshabilitar:

| Pareja escoge | Acción concreta en `agente_v2_heuristicas.py` |
|---|---|
| **EP** (Equivalence Partitioning) | En la función `construir_prompt()`, comenten el bloque `1. EQUIVALENCE PARTITIONING (EP):` y sus 4 líneas siguientes |
| **BVA** (Boundary Value Analysis) | Comenten el bloque `2. BOUNDARY VALUE ANALYSIS (BVA):` y sus 6 líneas siguientes |
| **DT** (Decision Tables) | Comenten el bloque `3. DECISION TABLES (DT):` y sus 2 líneas siguientes |

**Cómo comentar líneas en Python:** agreguen `#` al inicio de cada línea, o conviertan el bloque en string con triple comillas (`"""..."""`).

**Importante:** guarden el archivo después de modificarlo.

Ejecuten V2 modificado sobre el mismo Contract A:

```bash
python agente_v2_heuristicas.py
```

Comparen el nuevo `contract_b_v2_*.json` con el original (el de antes de modificar):
- ¿Cuántos escenarios menos generó?
- ¿Los tags de la heurística deshabilitada (ej: `@ep`, `@bva` o `@dt`) desaparecieron?
- ¿Qué tipo de escenarios específicamente se perdieron?

**Tip de seguridad:** si rompen el código y V2 no corre, restauren el bloque comentado y vuelvan a probar. El archivo `agente_v2_heuristicas.py` es de ustedes — pueden modificarlo libremente.

---

### Acción 3 — Diseñar AC rico vs AC pobre

> **Tiempo:** 10 minutos

Construyan **dos Contracts A pequeños**, cada uno con UNA user story y UN AC:

#### Contract A "rico" — un AC con todos los detalles posibles

Debe tener:
- **Rangos numéricos explícitos** (ej: "edad entre 18 y 99")
- **3-4 `test_data_examples`** distintos
- **2-3 `boundary_values`** listados
- Si aplica, **condiciones combinatorias** (ej: "si premium Y monto > X, descuento Y")

#### Contract A "pobre" — un AC vago, sin detalles

- **Una sola frase** (ej: "el sistema debe permitir cambiar la foto de perfil")
- Sin rangos, sin ejemplos, sin reglas

Pueden basarse en cualquier `contract_a_*.json` del Módulo 1 como plantilla — solo cambien el contenido para que apunte a sus dos casos.

Ejecuten V2 (versión **original**, NO la modificada de la Acción 2) sobre **cada Contract A**:

```bash
python agente_v2_heuristicas.py
```

(Cada vez les preguntará la ruta — la primera vez pasen el path del AC rico, la segunda vez el del AC pobre.)

Cuenten cuántos escenarios generó V2 para cada uno y anoten los números.

**Reflexionen:** la "limitación sutil" de V2 que les contó el docente — V2 amplifica lo que el AC tiene, no inventa donde no hay información.

---

## Entregable final

Al cerrar los 25 minutos, cada pareja prepara un reporte breve con:

| Sección | Contenido |
|---|---|
| **1. Tabla comparativa V1 vs V2** | Las 7 métricas calculadas correctamente (Acción 1) |
| **2. Heurística deshabilitada y observaciones** | Qué deshabilitaron, qué se perdió, números concretos (Acción 2) |
| **3. AC rico vs AC pobre — números** | Cantidad de escenarios para cada uno + breve interpretación (Acción 3) |
| **4. Lección personal** | ¿Qué entendieron del prompt engineering que NO sabían antes? |

---

## Comandos útiles

**Ejecutar V2 (original o modificado):**
```bash
python agente_v2_heuristicas.py
```

**Activar el venv si no está activo:**
```bash
# PowerShell (Windows)
.\venv\Scripts\Activate.ps1

# bash (Linux/Mac)
source venv/bin/activate
```

**Restaurar el archivo si lo rompieron al modificarlo:**
Usen el control de versiones de su editor (VS Code: `Ctrl+Z` para deshacer; o usen Git si lo tienen activo) para volver a la versión que funcionaba.

---

## Recordatorio

Esta práctica las hace **tocar el prompt directamente** — eso es lo que las separa de operadores casuales de IA y las acerca a ingenieras de calidad asistidas por IA. La calidad de su reporte depende de tres cosas:

1. Que las **métricas estén bien calculadas** desde los JSON.
2. Que el **modificar el prompt produzca un cambio observable** que ustedes puedan describir con números.
3. Que la **lección personal sea genuina** — qué entienden ahora del prompt engineering que antes no.

**Pregunten al docente cualquier duda durante los 25 minutos. La puesta en común al final es para compartir hallazgos, no para resolver dudas básicas.**

¡A modificar el prompt!
