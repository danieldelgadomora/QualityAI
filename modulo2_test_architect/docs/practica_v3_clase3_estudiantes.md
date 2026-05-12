# Práctica V3 — Auditoría humana de la matriz ISO 25010

> **Curso:** Calidad de Software y Pruebas Automatizadas
> **Módulo:** 2 — Test Architect Agent
> **Clase:** 3
> **Tiempo:** 25 minutos individuales en parejas + 10 minutos de puesta en común
> **Modalidad:** parejas con su propio computador, `GROQ_API_KEY` configurada y venv activo

---

## Contexto

Acaban de ver en presencial cómo V3 enriquece el prompt de V2 con un cuarto bloque de instrucciones: clasificar cada escenario con UNA característica ISO/IEC 25010, y producir una matriz de cobertura por característica. Saben en teoría que V3 entrega un "tablero" con `functional_suitability: 22, security: 4, usability: 0, ...` para responder al stakeholder.

En esta práctica van a **auditar esa matriz con ojo humano** — exactamente como un analista de QA en producción debería hacerlo antes de reportar al cliente. Porque la matriz **puede mentir** de dos maneras (falta real vs clasificación incompleta) y el LLM no sabe distinguirlas.

Esta es la práctica más cercana al rol que tendrán cuando salgan al mundo: el agente automatiza el 80%, el analista humano valida el 20% restante. Aprender a auditar es lo que las separa de operadoras de IA y las acerca a ingenieras de calidad asistidas por IA.

---

## Las 3 acciones que van a hacer

### Acción 1 — Auditoría humana de la matriz

> **Tiempo:** 10 minutos

Ejecuten V3 sobre el Contract A del registro/login del M1:

```bash
python agente_v3_iso25010.py
```

Apreten Enter para usar el Contract A de ejemplo. Esperen a que termine y se imprima el "tablero" de cobertura ISO 25010.

Abran el `contract_b_v3_*.json` recién generado. Por cada escenario, lean el campo `quality_characteristic` que el LLM asignó y **decidan si están de acuerdo o no**. Anoten en una tabla:

| Nombre del escenario (corto) | Clasificación del LLM | Su clasificación humana | ¿Coinciden? |
|---|---|---|---|
| Registro con email duplicado | functional_suitability | ? | ? |
| Registro con contraseña débil | security | ? | ? |
| ... | ... | ... | ... |

**Reglas para decidir como humanos** (no como el LLM):
- Si el escenario verifica el **texto exacto del mensaje** al usuario, hay un componente de **usability** — aunque también pruebe una regla de negocio.
- Si el escenario verifica **bloqueo de cuenta tras N intentos** o protección de credenciales, es **security** (no functional_suitability).
- Si verifica **tiempo de respuesta** o **carga concurrente**, es **performance_efficiency**.
- Si verifica **recuperación de fallas** o manejo de timeout, es **reliability**.

Al final de la Acción 1 calculen:

- **Total de escenarios revisados:** N
- **Escenarios donde coinciden con el LLM:** X
- **Escenarios donde discrepan:** Y
- **% de acuerdo:** X / N × 100

> *Tip:* en el AC del registro, presten atención especial a los escenarios cuyo `Then` verifica el TEXTO del mensaje al usuario. Esos son los candidatos a re-clasificar como `usability`.

---

### Acción 2 — Ajustar el prompt para reducir el sesgo

> **Tiempo:** 8 minutos

Han descubierto que el LLM tiene un **sesgo hacia `functional_suitability`** — es la categoría más fácil de defender, así que el LLM la usa por defecto. Vamos a corregirlo agregando una regla más explícita.

En `agente_v3_iso25010.py`, función `construir_prompt()`, busquen el bloque `## CLASIFICACION ISO/IEC 25010 (OBLIGATORIA)`.

En la sección `REGLAS PARA DECIDIR`, **agreguen una regla nueva** al final, antes del párrafo "NO asignes la categoria 'por defecto'":

```
   - Si el escenario verifica el TEXTO ESPECIFICO de un mensaje de error
     al usuario (no solo que el sistema rechace), tiene componente de
     usability — clasifica como usability cuando el foco principal del
     escenario sea la calidad del mensaje, no la regla en si.
```

Guarden el archivo y vuelvan a ejecutar V3 sobre el mismo Contract A:

```bash
python agente_v3_iso25010.py
```

Comparen la nueva matriz con la original (la de la Acción 1). Anoten:

| Característica | Matriz original | Matriz con prompt ajustado | Diferencia |
|---|---|---|---|
| functional_suitability | | | |
| security | | | |
| usability | | | |
| performance_efficiency | | | |
| ... | | | |

**Reflexionen:** ¿el prompt ajustado se acerca más a su auditoría humana de la Acción 1, o no? ¿En qué medida?

> *Tip de seguridad:* si rompen el prompt y V3 falla, restauren la regla agregada (bórrenla) y vuelvan a probar. El archivo es de ustedes — pueden modificarlo libremente.

---

### Acción 3 — Diseñar un AC que toque múltiples características

> **Tiempo:** 7 minutos

Construyan **un Contract A pequeño** con UNA user story y UN AC pensado deliberadamente para tocar **varias características ISO 25010** a la vez. Por ejemplo:

> *"El sistema procesa el pago con tarjeta de crédito en menos de 3 segundos, mostrando mensaje claro al usuario tras éxito o error, tolerante a fallas de red, y bloqueando la cuenta tras 5 intentos fallidos."*

Ese AC tiene implicaciones de:
- `functional_suitability` (procesar el pago)
- `performance_efficiency` (< 3 segundos)
- `usability` (mensaje claro)
- `reliability` (tolerancia a fallas de red)
- `security` (bloqueo tras 5 intentos)

Pueden usar como plantilla cualquier `contract_a_*.json` del Módulo 1. Solo ajusten un AC para que toque al menos **3 de las 8 características** ISO 25010.

Ejecuten V3 (versión **original**, NO la modificada en Acción 2) sobre su Contract A:

```bash
python agente_v3_iso25010.py
```

Cuando les pida la ruta, pasen el path de su Contract A nuevo.

**Auditen la matriz que sale.** ¿V3 logró distribuir los escenarios entre las características que ustedes esperaban? ¿Cuáles ignoró aunque el AC sí las tocaba?

> *Limitación esperada:* V3 va a tender a poner casi todo en `functional_suitability` y `security` aunque el AC pida más. Ese es justamente el sesgo que la Acción 2 trató de mitigar — y que V4 (HITL) viene a corregir definitivamente.

---

## Entregable final

Al cerrar los 25 minutos, cada pareja prepara un reporte breve con:

| Sección | Contenido |
|---|---|
| **1. Auditoría humana** | Tabla con N escenarios revisados + métricas: % de acuerdo con el LLM (Acción 1) |
| **2. Efecto del prompt ajustado** | Tabla comparativa de matrices antes/después + observación en una frase (Acción 2) |
| **3. AC multi-característica** | Su AC, la matriz que produjo V3, y qué características esperadas no fueron cubiertas (Acción 3) |
| **4. Lección personal** | ¿Por qué la matriz necesita ojo humano, en sus propias palabras? Conexión con V4 (HITL). |

---

## Comandos útiles

**Ejecutar V3 (original o modificado):**
```bash
python agente_v3_iso25010.py
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

**Buscar `quality_characteristic` rápido en el JSON:**
Usen `Ctrl+F` y busquen `"quality_characteristic":` para iterar por la clasificación de cada escenario.

---

## Recordatorio

Esta práctica las hace **auditar la salida del agente**, no solo correrlo. Eso es lo que las separa de operadoras de IA y las acerca a ingenieras de calidad asistidas por IA. La calidad de su reporte depende de tres cosas:

1. Que su **auditoría humana sea rigurosa** — escenario por escenario, no a vuelo de pájaro.
2. Que el **ajuste del prompt produzca un cambio observable** que puedan describir con números.
3. Que su **lección personal conecte la matriz con la necesidad de V4 (HITL)** — no quede en abstracto.

**Pregunten al docente cualquier duda durante los 25 minutos. La puesta en común al final es para compartir hallazgos, no para resolver dudas básicas.**

¡A auditar la matriz!
