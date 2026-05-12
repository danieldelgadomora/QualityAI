"""Serializers del Módulo 2: convierten modelos Pydantic a formatos externos.

La separación entre el schema (contract_b.py) y la serialización (este paquete)
respeta el principio de separación de concerns:
- contract_b.py define la ESTRUCTURA de los datos.
- serializers/ define cómo esos datos se TRANSFORMAN a formatos externos
  (texto .feature, JSON, Markdown, etc.).

Beneficios:
- El schema puede evolucionar sin tocar serialización.
- La serialización puede tener múltiples implementaciones (ej: serializar a
  Cucumber-style vs Behave-style) sin tocar el schema.
- Los tests de schema y los tests de serialización son independientes.
"""

from modulo2_test_architect.serializers.gherkin_writer import (
    feature_to_gherkin_text,
    suite_to_gherkin_files,
)

__all__ = [
    "feature_to_gherkin_text",
    "suite_to_gherkin_files",
]
