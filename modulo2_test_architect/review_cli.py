"""Agente v4 (M2): Human-in-the-Loop sobre el Contract B.

Esta es la cuarta version del agente del Modulo 2 — y la unica que NO
genera escenarios. V4 es un CLI de revision humana que opera sobre el
Contract B producido por V3, dando al analista de QA el control formal
sobre la clasificacion ISO 25010 y la aprobacion del suite antes de que
avance al Modulo 3 (Code Generator).

¿Por que V4 existe?
    Porque la matriz de cobertura ISO 25010 que produce V3 puede mentir.
    El LLM puede clasificar mal un escenario (ej: bloqueo tras N intentos
    como functional_suitability cuando es security), y la matriz no
    sabe distinguir un hueco real de una clasificacion incompleta.
    V4 incorpora al analista de QA como capa formal del pipeline:
    revisa cada escenario, corrige clasificaciones, registra justificaciones,
    y firma. Sin V4, el Contract B no es auditable bajo CMMI-DEV L3.

¿Que hace V4 concretamente?
    1. Carga un Contract B desde disco (tipicamente generado por V3).
    2. Itera escenario por escenario, mostrando al analista lo que el LLM clasifico.
    3. Permite al analista: aceptar, reclasificar, comentar o saltar.
    4. Cierra con una decision global: aprobar, rechazar o pedir cambios.
    5. Recalcula la matriz de cobertura si hubo reclasificaciones.
    6. Persiste el Contract B revisado como archivo NUEVO (versionado),
       preservando el original como evidencia.

Decisiones de diseño:
    - VERSIONAR (no mutar): el archivo original se preserva. El revisado
      se guarda con sufijo _reviewed para auditoria CMMI L3.
    - change_history GRANULAR: cada accion del analista deja un ReviewChange
      (timestamp, reviewer, action, notes). Auditable linea a linea.
    - BLOQUEANTE: el Modulo 3 debe validar review_status == APPROVED antes
      de procesar. Sin esa firma, el pipeline se detiene aqui.
    - SALIDA LIMPIA: si el analista interrumpe (q), el suite queda en
      pending_review y se puede retomar despues con otra ejecucion.

Limitaciones:
    - Monoseusuario: una sesion = un revisor. Para multi-revisor se requiere
      locking o conciliacion manual (V5+ posiblemente).
    - No persistente a mitad de revision: si interrumpes, empiezas de cero.
    - CLI por terminal — no UI web. Suficiente para analistas tecnicos de
      Katary; si product owners necesitan revisar, V5+ podria agregar UI.

Ejecutar:
    python review_cli.py
"""

import json
import os
import sys
import warnings
from copy import deepcopy
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore")

# Asegurar que la raiz del proyecto este en sys.path
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from modulo2_test_architect.src.contract_b import (
    GherkinScenario,
    GherkinTestSuite,
    QualityCharacteristic,
    ReviewChange,
    ReviewStatus,
)
from modulo2_test_architect.generate_acta import guardar_acta


# ============================================================
# UTILIDADES DE CONSOLA
# ============================================================
def imprimir_separador(char: str = "=", largo: int = 70):
    print(char * largo)


def imprimir_titulo(titulo: str):
    print()
    imprimir_separador("=")
    print(f" {titulo}")
    imprimir_separador("=")


def leer_input(prompt: str, default: str = "", obligatorio: bool = False) -> str:
    """Lee input del usuario con manejo limpio de Ctrl+C / EOF."""
    while True:
        try:
            valor = input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n[Sesion interrumpida — el suite queda en pending_review]")
            sys.exit(0)
        if not valor and default:
            return default
        if not valor and obligatorio:
            print("   Este campo es obligatorio. Intenta de nuevo.")
            continue
        return valor


# ============================================================
# PASO 1: Cargar Contract B desde JSON
# ============================================================
def cargar_contract_b(path: str) -> GherkinTestSuite:
    """Carga un Contract B desde disco y lo valida con Pydantic."""
    print(f"\nCargando Contract B desde: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    suite = GherkinTestSuite(**data)

    print(f"   Pipeline run ID: {suite.pipeline_run_id}")
    print(f"   Agente que lo produjo: {suite.agent_version}")
    print(f"   Total escenarios: {suite.total_scenarios}")
    print(f"   Estado actual: {suite.review.review_status.value}")
    return suite


# ============================================================
# PASO 2: Mostrar escenario al analista
# ============================================================
def mostrar_escenario(scenario: GherkinScenario, idx: int, total: int):
    """Imprime el escenario con su clasificacion actual."""
    print()
    imprimir_separador("-")
    print(f" Escenario {idx + 1} de {total}")
    imprimir_separador("-")
    print(f"   Nombre:                  {scenario.name}")
    print(f"   Tipo:                    {scenario.scenario_type.value}")
    print(f"   Clasificacion ISO 25010: {scenario.quality_characteristic.value}")
    print(f"   AC origen:               {scenario.acceptance_criterion_id}")
    print(f"   Tags:                    {', '.join(scenario.tags) if scenario.tags else '(sin tags)'}")
    print(f"   Pasos:")
    for step in scenario.steps:
        print(f"      {step.keyword:5s} {step.text}")


# ============================================================
# PASO 3: Acciones del analista por escenario
# ============================================================
def menu_iso25010() -> QualityCharacteristic:
    """Muestra las 8 caracteristicas y deja al analista escoger."""
    print()
    print("   Selecciona la caracteristica ISO 25010 correcta:")
    opciones = list(QualityCharacteristic)
    for i, qc in enumerate(opciones, 1):
        print(f"      {i}) {qc.value}")
    while True:
        elec = leer_input("   Numero [1-8]: ", obligatorio=True)
        try:
            n = int(elec)
            if 1 <= n <= 8:
                return opciones[n - 1]
        except ValueError:
            pass
        print("   Opcion invalida. Intenta de nuevo.")


def accion_reclasificar(
    scenario: GherkinScenario,
    reviewer: str,
    change_history: list[ReviewChange],
) -> bool:
    """Reclasifica un escenario y registra el cambio. Retorna True si hubo cambio."""
    nueva_qc = menu_iso25010()
    if nueva_qc == scenario.quality_characteristic:
        print(f"   La caracteristica seleccionada es la misma actual — sin cambios.")
        return False

    nota = leer_input(
        "   Razon del cambio (obligatoria para auditoria CMMI L3): ",
        obligatorio=True,
    )

    qc_anterior = scenario.quality_characteristic.value
    scenario.quality_characteristic = nueva_qc

    # Actualizar el tag @iso-* del escenario
    nuevo_tag = f"@iso-{nueva_qc.value.replace('_', '-')}"
    scenario.tags = [t for t in scenario.tags if not t.lower().startswith("@iso-")]
    if nuevo_tag not in scenario.tags:
        scenario.tags.append(nuevo_tag)

    change_history.append(
        ReviewChange(
            reviewer=reviewer,
            action="reclassified",
            notes=(
                f"Escenario '{scenario.name}': "
                f"{qc_anterior} -> {nueva_qc.value}. Razon: {nota}"
            ),
        )
    )
    print(
        f"   Reclasificado: {qc_anterior} -> {nueva_qc.value}. "
        f"Cambio registrado en change_history."
    )
    return True


def accion_comentar(
    scenario: GherkinScenario,
    reviewer: str,
    change_history: list[ReviewChange],
) -> bool:
    """Agrega un comentario sobre el escenario al change_history."""
    comentario = leer_input("   Comentario para el escenario: ", obligatorio=True)
    change_history.append(
        ReviewChange(
            reviewer=reviewer,
            action="comment_added",
            notes=f"Escenario '{scenario.name}': {comentario}",
        )
    )
    print(f"   Comentario registrado.")
    return False  # No modifica clasificacion


def accion_aceptar(
    scenario: GherkinScenario,
    reviewer: str,
    change_history: list[ReviewChange],
) -> bool:
    """Acepta la clasificacion del LLM tal cual. Registra la accion."""
    change_history.append(
        ReviewChange(
            reviewer=reviewer,
            action="accepted",
            notes=(
                f"Escenario '{scenario.name}': clasificacion "
                f"'{scenario.quality_characteristic.value}' confirmada por revisor."
            ),
        )
    )
    print(f"   Aceptado tal cual.")
    return False


# ============================================================
# PASO 4: Loop de revision escenario por escenario
# ============================================================
def revisar_escenarios(
    suite: GherkinTestSuite,
    reviewer: str,
    change_history: list[ReviewChange],
) -> int:
    """Itera por todos los escenarios y deja al analista decidir.

    Retorna la cantidad de escenarios reclasificados.
    """
    todos = [s for f in suite.features for s in f.scenarios]
    total = len(todos)
    cambios = 0

    imprimir_titulo(f"REVISION ESCENARIO POR ESCENARIO ({total} escenarios)")
    print(" Acciones disponibles por escenario:")
    print("   [a] aceptar la clasificacion del LLM (sin cambios)")
    print("   [r] reclasificar (escoger otra caracteristica ISO 25010)")
    print("   [c] solo agregar comentario (sin cambiar la clasificacion)")
    print("   [s] saltar (siguiente escenario, sin registrar accion)")
    print("   [q] salir de la sesion (suite queda en pending_review)")

    for idx, scenario in enumerate(todos):
        mostrar_escenario(scenario, idx, total)

        while True:
            opc = leer_input(
                "\n   Accion [a/r/c/s/q]: ",
                obligatorio=True,
            ).lower()
            if opc == "a":
                accion_aceptar(scenario, reviewer, change_history)
                break
            elif opc == "r":
                if accion_reclasificar(scenario, reviewer, change_history):
                    cambios += 1
                break
            elif opc == "c":
                accion_comentar(scenario, reviewer, change_history)
                break
            elif opc == "s":
                print("   Saltado (sin registro).")
                break
            elif opc == "q":
                print("\n   Sesion interrumpida — el suite queda en pending_review.")
                print(f"   Escenarios revisados antes de salir: {idx} de {total}")
                return cambios
            else:
                print("   Opcion no valida. Usa: a, r, c, s, q.")

    return cambios


# ============================================================
# PASO 5: Recalcular matriz de cobertura post-revision
# ============================================================
def recalcular_matriz(suite: GherkinTestSuite):
    """Recalcula coverage_by_characteristic despues de las reclasificaciones.

    Esto es CRITICO. Si el analista reclasifico 6 escenarios de
    functional_suitability a usability, la matriz original esta desactualizada
    y miente sobre el suite revisado. Hay que regenerarla.
    """
    todos = [s for f in suite.features for s in f.scenarios]
    nueva_matriz = {qc.value: 0 for qc in QualityCharacteristic}
    for s in todos:
        nueva_matriz[s.quality_characteristic.value] += 1
    suite.coverage_by_characteristic = nueva_matriz

    # Tambien actualizar quality_characteristics_covered en la coverage_matrix
    for cm in suite.coverage_matrix:
        scenarios_del_ac = [
            s for s in todos if s.acceptance_criterion_id == cm.criterion_id
        ]
        cm.quality_characteristics_covered = list(
            {s.quality_characteristic for s in scenarios_del_ac}
        )


def comparar_matrices(antes: dict[str, int], despues: dict[str, int]):
    """Imprime una tabla comparativa de la matriz antes/despues de revision."""
    imprimir_titulo("MATRIZ DE COBERTURA — ANTES VS DESPUES DE LA REVISION")
    print(f"   {'Caracteristica':<28} {'Antes':>8} {'Despues':>10} {'Delta':>8}")
    print(f"   {'-' * 28} {'-' * 8} {'-' * 10} {'-' * 8}")
    for qc in QualityCharacteristic:
        a = antes.get(qc.value, 0)
        d = despues.get(qc.value, 0)
        delta = d - a
        delta_str = f"+{delta}" if delta > 0 else (str(delta) if delta < 0 else "-")
        print(f"   {qc.value:<28} {a:>8} {d:>10} {delta_str:>8}")


# ============================================================
# PASO 6: Decision global del analista
# ============================================================
def decision_global(
    suite: GherkinTestSuite,
    reviewer: str,
    change_history: list[ReviewChange],
) -> ReviewStatus:
    """Pide al analista la decision final sobre el suite completo."""
    imprimir_titulo("DECISION GLOBAL SOBRE EL SUITE")
    print(" Opciones:")
    print("   [a] APROBAR    — el suite avanza al Modulo 3")
    print("   [r] RECHAZAR   — el suite NO avanza, requiere regenerarse")
    print("   [c] PEDIR CAMBIOS — aprobacion condicional (version sube y vuelve a V3)")

    while True:
        opc = leer_input("\n   Decision final [a/r/c]: ", obligatorio=True).lower()
        if opc in {"a", "r", "c"}:
            break
        print("   Opcion no valida.")

    feedback = leer_input(
        "   Comentario libre sobre el suite (opcional, Enter para omitir): ",
    )

    if opc == "a":
        nuevo_status = ReviewStatus.APPROVED
        suite.review.approved_by = reviewer
        suite.review.approved_at = datetime.now()
        action = "approved"
    elif opc == "r":
        nuevo_status = ReviewStatus.REJECTED
        action = "rejected"
    else:
        nuevo_status = ReviewStatus.NEEDS_CHANGES
        suite.review.version += 1
        action = "changes_requested"

    suite.review.review_status = nuevo_status
    if feedback:
        suite.review.analyst_feedback = feedback

    change_history.append(
        ReviewChange(
            reviewer=reviewer,
            action=action,
            notes=feedback or f"Decision final: {nuevo_status.value}",
        )
    )

    return nuevo_status


# ============================================================
# PASO 7: Persistir el Contract B revisado (versionado)
# ============================================================
def guardar_revisado(
    suite: GherkinTestSuite,
    original_path: Path,
) -> Path:
    """Guarda el Contract B revisado como archivo NUEVO (versionado).

    El archivo original se preserva intacto. El nuevo agrega sufijo
    _reviewed antes de .json. Asi un auditor puede comparar la salida
    cruda del LLM con la version firmada por el analista.
    """
    if original_path.stem.endswith("_reviewed"):
        # Si ya estabamos revisando un archivo revisado, incrementar version
        nuevo_path = original_path
    else:
        nuevo_path = original_path.with_name(f"{original_path.stem}_reviewed.json")

    nuevo_path.write_text(
        suite.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return nuevo_path


# ============================================================
# RESUMEN FINAL
# ============================================================
def imprimir_resumen(
    suite: GherkinTestSuite,
    cambios: int,
    output_path: Path,
):
    """Imprime el resumen final de la sesion."""
    imprimir_titulo("RESUMEN DE LA SESION DE REVISION")
    print(f"   Estado final del suite:    {suite.review.review_status.value}")
    print(f"   Version del suite:         {suite.review.version}")
    print(f"   Revisor:                   {suite.review.approved_by or '(no aprobado)'}")
    if suite.review.approved_at:
        print(f"   Fecha de aprobacion:       {suite.review.approved_at.isoformat()}")
    print(f"   Reclasificaciones:         {cambios}")
    print(f"   Total acciones registradas: {len(suite.review.change_history)}")
    print(f"   Archivo guardado en:       {output_path}")
    print()

    if suite.review.review_status == ReviewStatus.APPROVED:
        print(f"   El suite esta listo para avanzar al Modulo 3 (Code Generator).")
    elif suite.review.review_status == ReviewStatus.NEEDS_CHANGES:
        print(f"   El suite necesita cambios — vuelve a V3 con el feedback del analista.")
    elif suite.review.review_status == ReviewStatus.REJECTED:
        print(f"   El suite fue rechazado — debe regenerarse desde V3.")
    else:
        print(f"   El suite quedo en pending_review — puede retomarse despues.")


# ============================================================
# PIPELINE COMPLETO
# ============================================================
def pipeline_v4(contract_b_path: Path):
    """Ejecuta la sesion completa de revision humana."""
    imprimir_titulo("AGENTE M2-V4 — Human-in-the-Loop sobre el Contract B")
    print(" Revision humana del analista de QA sobre el Contract B producido por V3.")
    print(" Bloquea el avance al Modulo 3 hasta que el analista firme.")

    # Identificar al revisor — esto va al campo approved_by para auditoria
    reviewer = leer_input(
        "\n Identificador del revisor (ej: juanca.torres): ",
        obligatorio=True,
    )

    # Cargar y validar el Contract B
    suite = cargar_contract_b(str(contract_b_path))

    # Si ya estaba aprobado, advertir
    if suite.review.review_status == ReviewStatus.APPROVED:
        confirmar = leer_input(
            f"\n Atencion: el suite YA esta aprobado por {suite.review.approved_by}. "
            f"¿Reabrir revision? [s/n]: ",
            default="n",
        ).lower()
        if confirmar != "s":
            print(" Sesion cancelada — el suite mantiene su estado actual.")
            return

    # Capturar matriz original para comparacion despues
    matriz_original = deepcopy(suite.coverage_by_characteristic)

    # Lista local de cambios — al final se sincroniza con suite.review.change_history
    change_history_nueva: list[ReviewChange] = []

    # Loop de revision
    cambios = revisar_escenarios(suite, reviewer, change_history_nueva)

    # Recalcular matriz si hubo reclasificaciones
    if cambios > 0:
        recalcular_matriz(suite)
        comparar_matrices(matriz_original, suite.coverage_by_characteristic)
    else:
        print(f"\n No hubo reclasificaciones — la matriz se mantiene igual.")

    # Decision global
    decision_global(suite, reviewer, change_history_nueva)

    # Persistir change_history en el suite (al final, despues de toda la sesion)
    suite.review.change_history.extend(change_history_nueva)

    # Guardar archivo versionado
    output_path = guardar_revisado(suite, contract_b_path)

    # Generar acta HTML para entrega al cliente
    acta_path = guardar_acta(suite, output_path)

    # Resumen
    imprimir_resumen(suite, cambios, output_path)
    print(f"   Acta HTML generada en:     {acta_path}")


# ============================================================
# EJECUCION
# ============================================================
if __name__ == "__main__":
    print()
    print("Bienvenido a review_cli.py — V4 del Test Architect (HITL)")
    print()

    contract_b_path_str = leer_input(
        "Ruta al Contract B JSON a revisar (Enter para listar disponibles):\n> ",
    )

    if not contract_b_path_str:
        # Listar disponibles en output/
        output_dir = Path(__file__).parent / "output"
        if not output_dir.exists():
            print(f"Error: directorio {output_dir} no existe.")
            sys.exit(1)
        archivos = sorted(output_dir.glob("contract_b_*.json"))
        if not archivos:
            print(f"Error: no hay archivos contract_b_*.json en {output_dir}")
            sys.exit(1)
        print()
        print("Contract B disponibles en output/:")
        for i, f in enumerate(archivos, 1):
            print(f"   {i}) {f.name}")
        elec = leer_input("\n Numero del archivo a revisar: ", obligatorio=True)
        try:
            contract_b_path = archivos[int(elec) - 1]
        except (ValueError, IndexError):
            print("Eleccion invalida.")
            sys.exit(1)
    else:
        contract_b_path = Path(contract_b_path_str)

    if not contract_b_path.exists():
        print(f"Error: archivo no encontrado: {contract_b_path}")
        sys.exit(1)

    pipeline_v4(contract_b_path)
