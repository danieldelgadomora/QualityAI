"""Contract A — entrada del Módulo 2 (re-export desde Módulo 1).

Este archivo es el ÚNICO punto de acoplamiento del Módulo 2 con el Módulo 1.
Re-exporta las clases del Contract A definido en modulo1_requirements_refiner.

Decisión arquitectónica (ADR-M2-001):
- El Contract A se define UNA SOLA VEZ en el Módulo 1.
- Módulo 2 lo importa desde aquí, no duplica el schema.
- El resto del código del Módulo 2 importa desde este archivo, no directamente
  desde Módulo 1.
- Esto centraliza el acoplamiento entre módulos en un solo punto: si el
  Contract A cambia, solo este archivo necesita ajuste; el resto del Módulo 2
  no se entera.

Por qué un re-export en lugar de simplemente importar desde modulo1:
- Aislamiento del cambio: si en el futuro cambiamos la fuente del Contract A
  (versionado, migración, etc.), solo este archivo cambia.
- Documentación: este archivo declara EXPLÍCITAMENTE qué del Módulo 1 usa el
  Módulo 2.
- Testing: si el Contract A evoluciona y rompe contrato con M2, los tests
  detectan la incompatibilidad en un solo lugar.

Cómo ejecutar el código que importa desde aquí:
- Desde la raíz del proyecto QualityAI/, con PYTHONPATH apuntando a esa raíz.
- Ejemplo: `cd QualityAI && python -m modulo2_test_architect.src.algun_modulo`
"""

from __future__ import annotations

import sys
from pathlib import Path

# Asegurar que la raíz del proyecto está en PYTHONPATH para importar modulo1.
# Esto permite ejecutar el código sin necesidad de configurar PYTHONPATH manualmente.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Re-exportar el Contract A del Módulo 1
from modulo1_requirements_refiner.src.contract_a import (  # noqa: E402
    AcceptanceCriterion,
    AmbiguityResolution,
    Priority,
    RefinedRequirements,
    StoryType,
    UserStory,
)

# __all__ explícito documenta qué del Contract A consume el Módulo 2.
__all__ = [
    "AcceptanceCriterion",
    "AmbiguityResolution",
    "Priority",
    "RefinedRequirements",
    "StoryType",
    "UserStory",
]
