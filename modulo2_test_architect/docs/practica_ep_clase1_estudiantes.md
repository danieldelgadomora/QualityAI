# Práctica EP — Validación del campo "contraseña" en Katary360

> **Curso:** Calidad de Software y Pruebas Automatizadas
> **Módulo:** 2 — Test Architect Agent
> **Clase:** 1 — Técnicas de diseño de pruebas caja negra
> **Técnica que aplica:** Equivalence Partitioning (EP)
> **Tiempo:** 20 minutos individuales + 10 minutos de puesta en común

---

## Contexto

Estás diseñando los casos de prueba para el campo **"contraseña"** del formulario de registro del sistema **Katary360**. El equipo de seguridad definió las siguientes reglas:

- **Longitud:** entre 8 y 64 caracteres inclusive.
- **Composición obligatoria:** debe contener al menos 1 letra mayúscula, 1 letra minúscula, 1 número y 1 carácter especial (de este conjunto: `@ # $ % & * ! ?`).
- **Restricción adicional:** no puede contener espacios.
- **Obligatoriedad:** el campo es requerido (no puede estar vacío).

---

## Tu tarea

Aplica la técnica de **Equivalence Partitioning** siguiendo el método de los 4 pasos visto en clase:

1. Identifica el dominio del problema (todos los valores posibles para el campo).
2. Identifica las **clases válidas** (combinaciones de valores que cumplen TODAS las reglas).
3. Identifica las **clases inválidas** (cada regla violada genera al menos una clase inválida).
4. Diseña UN caso de prueba concreto por cada clase identificada.

Entrega una tabla con las siguientes columnas:

| # | Tipo (Válida / Inválida) | Descripción de la clase | Ejemplo concreto de valor |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| ... | | | |

---

## Restricciones de la entrega

- Cada clase debe corresponder a **UNA regla violable independiente**. No agrupes múltiples reglas en una sola clase.
- El **ejemplo concreto** debe pertenecer realmente a la clase declarada (verificable por inspección).
- Aplica los 4 pasos del método con disciplina, no improvises.
- Justifica tu decisión si fusionas o separas clases borderline.

---

## Recordatorios

- **Una clase por regla violable:** si "no cumple complejidad" cubre 4 reglas distintas (mayúscula, minúscula, número, carácter especial), entonces son **4 clases inválidas**, no 1.
- **El campo vacío** puede ser una clase distinta de "longitud menor a 8" — el sistema generalmente da un mensaje de error específico para campo requerido.
- **Verificación rápida del ejemplo:** lee tu ejemplo y pregúntate "¿este valor realmente viola SOLO la regla que dice mi descripción, o también viola otras?" Si viola varias, busca otro ejemplo más limpio.

---

## Después de los 20 minutos

Tu profesor proyectará la solución de un voluntario y la clase auditará en conjunto. Prepárate para que tu solución sea esa — y prepárate también para auditar a un compañero aplicando criterios técnicos, no opinión.

¡A diseñar pruebas!
