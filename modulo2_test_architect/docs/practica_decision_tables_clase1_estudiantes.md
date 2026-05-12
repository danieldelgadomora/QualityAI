# Práctica Decision Tables — Aprobación de horas extra en Katary

> **Curso:** Calidad de Software y Pruebas Automatizadas
> **Módulo:** 2 — Test Architect Agent
> **Clase:** 1 — Técnicas de diseño de pruebas caja negra
> **Técnica que aplica:** Decision Tables (incluyendo reducción con "don't care")
> **Tiempo:** 20 minutos individuales + 10 minutos de puesta en común
> **Pre-requisito:** ya completaste las prácticas de EP y BVA

---

## Contexto

Katary tiene un sistema automático de aprobación de horas extra para sus colaboradores. Las reglas que el área de **Recursos Humanos** definió son:

1. Si el colaborador es **de planta** Y ha trabajado **8 horas o más** en el día Y el **jefe directo aprobó** la solicitud: **AUTORIZADAS Y PAGADAS AL 150%** (con recargo nocturno).

2. Si el colaborador es de planta Y ha trabajado **menos de 8 horas** en el día (sale temprano y regresa) Y el jefe directo aprobó: **AUTORIZADAS Y PAGADAS AL 100%** (sin recargo, son horas regulares de complemento).

3. Si el colaborador es de planta pero el jefe directo **NO aprobó**: **NO AUTORIZADAS** (sin importar las horas trabajadas).

4. Si el colaborador **NO es de planta** (es contratista o externo): **NO AUTORIZADAS** sin importar las demás condiciones (los contratistas se rigen por sus propios contratos).

---

## Tu tarea — en cuatro pasos

### Paso 1 — Identifica condiciones y acciones del sistema

Lista las **condiciones** binarias (Sí / No) que el sistema evalúa, y las **acciones** posibles que toma como resultado.

**Condiciones:**

- C1: ?
- C2: ?
- C3: ?

**Acciones:**

- ?
- ?
- ?

---

### Paso 2 — Construye la tabla completa con todas las combinaciones binarias

No te preocupes por las acciones todavía, solo enumera las combinaciones.

> **Pista:** 3 condiciones binarias = **2³ = 8 combinaciones**.

| Regla | C1 | C2 | C3 | Acción |
|---|---|---|---|---|
| R1 | | | | ? |
| R2 | | | | ? |
| R3 | | | | ? |
| R4 | | | | ? |
| R5 | | | | ? |
| R6 | | | | ? |
| R7 | | | | ? |
| R8 | | | | ? |

---

### Paso 3 — Llena las acciones según las 4 reglas del negocio

Para cada combinación, identifica qué regla del negocio le aplica y cuál es la acción resultante. **Si encuentras alguna combinación que el requerimiento NO especifica, márcala como `GAP DE REQUERIMIENTO`** — es un hallazgo de calidad para devolver al analista.

| Regla | C1 | C2 | C3 | Acción | Aplicó regla |
|---|---|---|---|---|---|
| R1 | | | | | |
| R2 | | | | | |
| ... | | | | | |

---

### Paso 4 — Reduce la tabla aplicando "don't care"

Aplica la reducción **iterativamente**: después de cada colapso, releé la tabla y busca **nuevos colapsos** hasta que no haya más posibles.

Una regla se puede colapsar cuando dos o más combinaciones producen la **misma acción** y solo difieren en una condición. Esa condición se marca como `-` (don't care).

> **Aviso importante:** la reducción es iterativa. Hay un colapso "obvio" pero también hay un colapso menor. **No te quedes solo con el primero.**

**Tabla reducida final:**

| Regla | C1 | C2 | C3 | Acción |
|---|---|---|---|---|
| RR1 | | | | |
| RR2 | | | | |
| ... | | | | |

---

## Cierre — Casos de prueba finales

Lista los **casos de prueba concretos** derivados de tu tabla reducida. Cada caso debe tener valores específicos (no `-`) para poder ejecutarse.

| TC | C1 | C2 | C3 | Resultado esperado |
|---|---|---|---|---|
| TC1 | | | | |
| TC2 | | | | |
| ... | | | | |

---

## Restricciones importantes

- **No inventes resultados.** Si una combinación no está en el requerimiento, márcala como `GAP DE REQUERIMIENTO`. Es un hallazgo de calidad real, no una falla tuya.
- **Reducción iterativa:** después del primer colapso, vuelve a recorrer la tabla. Es muy probable que haya más colapsos posibles.
- **Casos de prueba concretos:** el `-` en la tabla reducida representa "cualquiera"; en los casos de prueba debes escoger un valor específico para cada `-`.

---

## Recordatorios

- **EP** se aplica a un campo aislado. **BVA** refina los valores específicos dentro de un campo. **Decision Tables** se aplica cuando el resultado depende de la **combinación** de varios campos. Las tres son complementarias, no alternativas.
- **2³ = 8 combinaciones** es lo correcto para 3 condiciones binarias. Si te dan más combinaciones, revisa si duplicaste alguna.
- En este caso particular **no hay gaps** (las 4 reglas del negocio cubren las 8 combinaciones), pero en otros casos sí podrías encontrarlos.

---

## Después de los 20 minutos

Tu profesor proyectará la solución de un voluntario. La clase auditará en conjunto verificando:
- Si las 3 condiciones y las 3 acciones están bien identificadas.
- Si el mapeo de las 8 acciones es consistente con las 4 reglas del negocio.
- Si se aplicó **reducción iterativa completa** o solo se quedó en el primer colapso.

Prepárate para mostrar el camino de tu reducción, no solo el resultado final.

¡A construir tablas de decisión!
