# Práctica BVA — Refinamiento de la validación del campo "contraseña"

> **Curso:** Calidad de Software y Pruebas Automatizadas
> **Módulo:** 2 — Test Architect Agent
> **Clase:** 1 — Técnicas de diseño de pruebas caja negra
> **Técnica que aplica:** Boundary Value Analysis (BVA-2)
> **Tiempo:** 15 minutos individuales + 10 minutos de puesta en común
> **Pre-requisito:** ya completaste la práctica de Equivalence Partitioning sobre el mismo caso

---

## Contexto

Estás en el **mismo caso** que en la práctica anterior de EP (campo "contraseña" del registro de Katary360). Recuerda las reglas:

- **Longitud:** entre 8 y 64 caracteres inclusive.
- **Composición:** al menos 1 mayúscula, 1 minúscula, 1 número, 1 carácter especial (`@ # $ % & * ! ?`).
- **Restricción:** no puede contener espacios.
- **Obligatorio.**

En la práctica anterior identificaste **9 clases de equivalencia**. Ahora vas a **refinar tu suite de pruebas aplicando BVA**.

---

## Tu tarea — en tres partes

### Parte 1 — Identificar dimensiones donde BVA aplica

El campo "contraseña" tiene varias reglas. Identifica cuáles tienen **bordes** (es decir, son medibles en una escala con mínimo y máximo) y cuáles son reglas **booleanas o categóricas** (sin bordes naturales).

Construye una tabla:

| Regla | ¿Tiene bordes? | ¿BVA aplica? |
|---|---|---|
| Longitud entre 8 y 64 caracteres | | |
| Al menos 1 mayúscula | | |
| Al menos 1 minúscula | | |
| Al menos 1 número | | |
| Al menos 1 carácter especial | | |
| Sin espacios | | |
| Obligatorio | | |

---

### Parte 2 — Aplicar BVA-2 a la(s) dimensión(es) ordenable(s)

Para cada dimensión donde BVA aplica, lista los **valores específicos a probar** siguiendo el método BVA-2 (los 4 valores frontera: límite inferior, justo debajo, límite superior, justo encima).

Para cada valor, da un **ejemplo concreto de contraseña** que cumpla **todas las demás reglas** (composición, sin espacios) y solo varíe en la dimensión que estás probando.

| # | Longitud | Ejemplo concreto (cumpliendo demás reglas) | Validez |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |

---

### Parte 3 — Mapear cobertura

Construye una tabla con dos columnas:

**Clases de EP cubiertas automáticamente por tus valores BVA** (de las 9 clases originales):

| Valor BVA | Clase de EP cubierta |
|---|---|
| | |
| | |

**Clases de EP que siguen requiriendo casos separados** (las que BVA no toca):

| Clase de EP | Por qué BVA no la cubre | Ejemplo de caso adicional |
|---|---|---|
| | | |
| | | |

---

## Restricciones importantes

- **Cada ejemplo BVA debe cumplir TODAS las demás reglas** para que el resultado del test sea atribuible específicamente al borde de longitud. Si pones una contraseña de 7 caracteres sin mayúscula, no sabes si el sistema la rechazó por longitud o por composición. **Aislar variables es ingeniería pura.**
- BVA aplica solo a dimensiones **ordenables** (rangos numéricos, longitudes, tamaños, fechas). NO aplica a reglas booleanas o categóricas.

---

## Recordatorios

- Los 4 valores BVA-2 para un rango `[mín, máx]` son: `mín-1`, `mín`, `máx`, `máx+1`.
- El campo **vacío** (longitud 0) es un caso aparte — BVA prueba con valores **con contenido**, no con vacío. La clase "vacío" sigue requiriendo su propio caso.
- Al final de la práctica deberías tener **10 casos de prueba** del campo "contraseña" en total: **4 valores BVA + 6 valores EP adicionales** (composición + espacios + vacío).

---

## Después de los 15 minutos

Tu profesor proyectará la solución de un voluntario. La clase auditará en conjunto verificando:
- Si BVA se aplicó correctamente solo a longitud.
- Si los ejemplos concretos son verdaderamente "limpios" (no mezclan variables).
- Si quedó claro qué clases siguen huérfanas y por qué.

Prepárate para argumentar tus decisiones.

¡A refinar la suite!
