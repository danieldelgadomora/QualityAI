"""Serialización de modelos Gherkin a texto .feature.

Convierte instancias de GherkinFeature (definidas en contract_b.py) a texto
de archivos .feature parseables por cualquier runner BDD estándar
(Cucumber, Behave, SpecFlow, etc.).

La separación de este módulo respecto a contract_b.py implementa el principio
de separación de concerns:
- contract_b.py: define qué datos existen (estructura).
- gherkin_writer.py: define cómo esos datos se vuelven texto (serialización).

Si en el futuro queremos serializar al formato Cucumber-JSON, agregamos otra
función aquí (o un módulo hermano) sin tocar el schema.
"""

from __future__ import annotations

from modulo2_test_architect.src.contract_b import (
    GherkinFeature,
    GherkinTestSuite,
)


def feature_to_gherkin_text(feature: GherkinFeature) -> str:
    """Convierte un GherkinFeature a texto .feature parseable.

    El texto generado es válido según la sintaxis Gherkin estándar y puede
    ejecutarse con runners BDD como Behave, Cucumber, SpecFlow, etc.

    Args:
        feature: instancia de GherkinFeature con escenarios completos.

    Returns:
        Cadena con el contenido del archivo .feature listo para escribir a disco.
    """
    lines: list[str] = []

    # Tags de la feature (si los hay)
    if feature.tags:
        lines.append(" ".join(feature.tags))

    # Cabecera de la feature
    lines.append(f"Feature: {feature.name}")
    lines.append(f"  {feature.description}")
    lines.append("")

    # Background (pasos comunes a todos los escenarios)
    if feature.background:
        lines.append("  Background:")
        for step in feature.background:
            lines.append(f"    {step.keyword} {step.text}")
        lines.append("")

    # Escenarios
    for scenario in feature.scenarios:
        # Tags del escenario
        if scenario.tags:
            lines.append(f"  {' '.join(scenario.tags)}")

        # Tipo de escenario (Scenario o Scenario Outline)
        keyword = "Scenario Outline" if scenario.is_outline else "Scenario"
        lines.append(f"  {keyword}: {scenario.name}")

        # Pasos del escenario
        for step in scenario.steps:
            lines.append(f"    {step.keyword} {step.text}")

            # Tabla de datos asociada al paso (si existe)
            if step.data_table:
                headers = list(step.data_table[0].keys())
                lines.append(f"      | {' | '.join(headers)} |")
                for row in step.data_table:
                    values = [str(row[h]) for h in headers]
                    lines.append(f"      | {' | '.join(values)} |")

        # Tabla de Examples (solo para Scenario Outline)
        if scenario.is_outline and scenario.examples:
            lines.append("")
            lines.append("    Examples:")
            lines.append(f"      | {' | '.join(scenario.examples.headers)} |")
            for row in scenario.examples.rows:
                lines.append(f"      | {' | '.join(row)} |")

        lines.append("")

    return "\n".join(lines)


def suite_to_gherkin_files(suite: GherkinTestSuite) -> dict[str, str]:
    """Convierte un GherkinTestSuite completo a múltiples archivos .feature.

    Cada feature del suite se serializa como un archivo .feature independiente.
    El nombre del archivo se deriva de la user_story_id.

    Args:
        suite: instancia de GherkinTestSuite con una o más features.

    Returns:
        Diccionario con clave = nombre de archivo .feature y valor = contenido
        del archivo. El consumidor decide dónde escribirlos.

    Ejemplo:
        files = suite_to_gherkin_files(suite)
        for filename, content in files.items():
            (output_dir / filename).write_text(content, encoding="utf-8")
    """
    files: dict[str, str] = {}
    for feature in suite.features:
        # Convención: el nombre del archivo deriva del user_story_id
        # (ej: US-001 → US-001.feature)
        filename = f"{feature.user_story_id}.feature"
        files[filename] = feature_to_gherkin_text(feature)

    return files
