# Guía de Estudio — Prework Módulo 2

> **Curso:** Calidad de Software y Pruebas Automatizadas — Especialización en Construcción de Software, Universidad de Nariño
> **Tiempo estimado de estudio:** 2 a 3 horas
> **Validación:** Quiz vinculante al inicio de Clase 1. Umbral mínimo **70% (7 de 10 preguntas correctas)** para participar de la sesión práctica.

---

## Cómo prepararte para el quiz

1. **Estudia los 6 temas listados abajo** consultando las fuentes recomendadas. No improvises con resultados aleatorios de Google — las fuentes acá son curadas para garantizar consistencia.
2. **Toma notas con tus propias palabras**, no copies textual. La regla: si no lo puedes explicar simple, no lo entendiste.
3. **Trae el quiz desarrollado en tu cabeza, no en papel.** El quiz se hace en clase, en tu computador, con auto-validación. Los resultados son individuales.
4. **Si tienes dudas conceptuales, escríbelas y tráelas a clase.** No es vergüenza; es responsabilidad profesional.

---

## Los 6 temas que el quiz va a evaluar

### Tema 1 — Testing vs Debugging vs Quality Assurance/Control

**Lo que debes dominar:**
Distinguir con precisión 4 conceptos que la industria mezcla todo el tiempo. Quality Assurance (QA) es proceso preventivo orientado a cómo trabajar bien. Quality Control (QC) es producto reactivo, verifica que el entregable cumpla. Testing es una de las actividades del QC. Debugging es la respuesta del desarrollador cuando se reporta un fallo. Además, distinguir Static Testing (no se ejecuta el código bajo prueba — linters, revisiones) vs Dynamic Testing (sí se ejecuta — pytest, app corriendo).

**Fuentes recomendadas:**
- ISTQB CTFL v4.0 Syllabus, secciones **1.1 y 1.2** — descarga gratis en https://www.istqb.org/certifications/certified-tester-foundation-level
- Versión en español del syllabus: https://hastqb.org/programa-de-estudio-nivel-basico/
- Artículo introductorio: https://www.guru99.com/software-testing-introduction-importance.html

---

### Tema 2 — Los 7 Principios Fundamentales del Testing

**Lo que debes dominar:**
Los 7 principios oficiales según ISTQB. Recomendado memorizarlos agrupados pedagógicamente: **Límites** (P1 las pruebas evidencian la presencia de defectos no su ausencia, P2 las pruebas exhaustivas son imposibles, P7 falacia de ausencia de defectos), **Estrategia** (P3 testing temprano ahorra tiempo y dinero, P4 los defectos se agrupan, P6 testing depende del contexto), **Vida** (P5 paradoja del pesticida — las pruebas se desgastan).

**Fuentes recomendadas:**
- ISTQB CTFL v4.0 Syllabus, sección **1.3** (es la sección más densa pero más rentable del syllabus)
- Artículo: https://www.tutorialspoint.com/software_testing/software_testing_principles.htm
- Video corto (10 min): buscar en YouTube "ISTQB Foundation 7 Principles of Testing"

---

### Tema 3 — El Proceso de Prueba (7 actividades)

**Lo que debes dominar:**
Las 7 actividades del proceso de prueba según ISTQB: Test Planning, Test Monitoring & Control (corre en paralelo a todo el proceso), Test Analysis (qué probar), Test Design (cómo probarlo), Test Implementation (preparar ambiente y datos), Test Execution (correr los tests), Test Completion (cierre, lecciones aprendidas, archivado). Importante entender que son **actividades, no fases secuenciales** — pueden traslaparse y iterar.

**Fuentes recomendadas:**
- ISTQB CTFL v4.0 Syllabus, sección **1.4**
- Artículo: https://www.softwaretestinghelp.com/test-process/

---

### Tema 4 — Niveles de Prueba

**Lo que debes dominar:**
Los 4 niveles principales: **Unitario** (función o clase aislada, hecho por desarrollador), **Integración** (interacción entre módulos), **Sistema** (end-to-end con el sistema completo en ambiente similar a producción) y **Aceptación** (validado por el cliente o usuario final contra criterios de negocio). Adicionalmente: la **Pirámide de Pruebas** de Mike Cohn — muchas unitarias en la base, pocas E2E en la punta. Anti-patrón a reconocer: el "cono de helado invertido".

**Fuentes recomendadas:**
- ISTQB CTFL v4.0 Syllabus, sección **2.2**
- Artículo clásico de Martin Fowler sobre la pirámide: https://martinfowler.com/articles/practical-test-pyramid.html
- Video: buscar "Mike Cohn Test Pyramid" en YouTube

---

### Tema 5 — Tipos de Prueba

**Lo que debes dominar:**
Las 3 grandes categorías de tipos según ISTQB: **Funcional** (¿qué hace el sistema?, alineado con la característica "Functional Suitability" de ISO 25010), **No Funcional** (¿cómo lo hace?, alineado con las otras 7 características de ISO 25010 — performance, security, usability, reliability, compatibility, maintainability, portability), y **Relacionada con Cambios** que se subdivide en Confirmation Testing (re-test después de un fix) y Regression Testing (verificar que un cambio no rompió nada más).

**Fuentes recomendadas:**
- ISTQB CTFL v4.0 Syllabus, sección **2.3**
- Resumen de ISO 25010: https://iso25000.com/index.php/normas-iso-25000/iso-25010
- Artículo sobre confirmación vs regresión: https://www.guru99.com/regression-testing.html

---

### Tema 6 — Clasificación de Técnicas

**Lo que debes dominar:**
Las 3 categorías de técnicas de diseño de pruebas según ISTQB: **Caja Negra / Specification-based** (diseño desde la especificación, sin ver código — Equivalence Partitioning, BVA, Decision Tables, State Transition), **Caja Blanca / Structure-based** (diseño desde el código, midiendo cobertura — Statement, Branch), y **Basadas en Experiencia** (diseño desde memoria profesional del tester — Error Guessing, Exploratory Testing, Checklist-based). Las tres son complementarias, no excluyentes; un equipo maduro las combina.

**Fuentes recomendadas:**
- ISTQB CTFL v4.0 Syllabus, secciones **4.1, 4.2, 4.3 y 4.4** (panorámico, no necesitas dominar las técnicas en profundidad — eso lo veremos en Clase 1 presencial)
- Artículo introductorio: https://www.softwaretestinghelp.com/black-box-testing/

---

## Recordatorios finales

- **El quiz es vinculante.** No es un trámite. Reprobar bloquea tu participación en la sesión práctica.
- **El quiz tiene 10 preguntas, una sola correcta por pregunta.** Cubre los 6 temas con distribución equilibrada.
- **Si fallas el quiz, recibirás feedback de qué tema(s) debes repasar y podrás reintentar después de un intervalo corto** (decidido en clase según el caso).
- **Trae preguntas conceptuales a clase.** Las dudas honestas se resuelven; los huecos disimulados se acumulan.
