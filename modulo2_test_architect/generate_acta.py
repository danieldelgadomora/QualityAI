"""Generador de Acta de Aprobación de Pruebas (HTML).

Toma un Contract B revisado (producido por V4/review_cli.py) y genera un
documento HTML autónomo listo para entregar al cliente y ser firmado.

El acta incluye:
    1. Encabezado institucional con estado y versión del suite.
    2. Información del revisor y su decisión.
    3. Resumen ejecutivo con contexto de requerimientos (US, features, ACs).
    4. Tabla de cobertura ISO 25010 con barras visuales.
    5. Clasificación de riesgos por atributo de calidad ISO 25010.
    6. Inventario de escenarios por feature.
    7. Matriz de trazabilidad AC → Escenarios.
    8. Historial de revisión (auditoría CMMI L3).
    9. Bloque de firma para el cliente.

Ejecutar:
    python generate_acta.py
    python generate_acta.py output/contract_b_v3_..._reviewed.json
"""

import html
import json
import sys
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore")

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from modulo2_test_architect.src.contract_b import (
    GherkinTestSuite,
    QualityCharacteristic,
    ReviewStatus,
)


# ============================================================
# HELPERS
# ============================================================
_STATUS_LABELS = {
    ReviewStatus.APPROVED: ("APROBADO", "#1a7f37"),
    ReviewStatus.REJECTED: ("RECHAZADO", "#cf222e"),
    ReviewStatus.NEEDS_CHANGES: ("REQUIERE CAMBIOS", "#9a6700"),
    ReviewStatus.PENDING_REVIEW: ("PENDIENTE DE REVISIÓN", "#6e7781"),
}

_ISO_LABELS = {
    "functional_suitability": "Idoneidad Funcional",
    "performance_efficiency": "Eficiencia de Desempeño",
    "compatibility": "Compatibilidad",
    "usability": "Usabilidad",
    "reliability": "Fiabilidad",
    "security": "Seguridad",
    "maintainability": "Mantenibilidad",
    "portability": "Portabilidad",
}

_TYPE_LABELS = {
    "positive": "Positivo",
    "negative": "Negativo",
    "boundary": "Frontera",
    "edge_case": "Caso Extremo",
    "error_handling": "Manejo de Error",
}

_TYPE_COLORS = {
    "positive": "#1a7f37",
    "negative": "#cf222e",
    "boundary": "#0550ae",
    "edge_case": "#9a6700",
    "error_handling": "#8250df",
}

_ISO_DESCRIPTIONS = {
    "functional_suitability": "Verifica que el sistema realiza correctamente todas las funciones solicitadas y produce los resultados esperados en cada operación.",
    "performance_efficiency": "Evalúa que el sistema responde con rapidez, incluso cuando muchos usuarios lo utilizan al mismo tiempo.",
    "compatibility": "Comprueba que el sistema funciona correctamente en los navegadores, dispositivos y versiones de software declarados.",
    "usability": "Valida que el sistema es fácil de usar, intuitivo y accesible para todos los usuarios finales.",
    "reliability": "Confirma que el sistema opera sin interrupciones y se recupera correctamente ante fallos técnicos.",
    "security": "Verifica que el sistema protege los datos sensibles y solo permite acceso a usuarios autorizados.",
    "maintainability": "Asegura que el sistema puede actualizarse y corregirse sin generar nuevos problemas.",
    "portability": "Confirma que el sistema puede instalarse y operar en todos los entornos tecnológicos requeridos.",
}

_ISO_RIESGOS = {
    "functional_suitability": {
        "impacto": "El sistema podría incumplir requerimientos funcionales, producir resultados incorrectos o fallar en flujos críticos de negocio.",
        "recomendacion": "Verificar cobertura completa de todos los criterios de aceptación funcionales antes de pasar a producción.",
    },
    "performance_efficiency": {
        "impacto": "Tiempos de respuesta degradados, cuellos de botella bajo carga concurrente y posible pérdida de usuarios por latencia inaceptable.",
        "recomendacion": "Incluir pruebas de carga y stress para validar los SLAs de rendimiento definidos en los requerimientos.",
    },
    "compatibility": {
        "impacto": "El sistema podría fallar en entornos de destino (navegadores, sistemas operativos, versiones de API, integraciones externas).",
        "recomendacion": "Agregar escenarios que validen el comportamiento en cada entorno y combinación de versiones declarados.",
    },
    "usability": {
        "impacto": "Usuarios finales con dificultad para operar el sistema, incremento de errores de operación y carga de soporte.",
        "recomendacion": "Incorporar pruebas de flujo end-to-end desde la perspectiva del usuario con criterios de accesibilidad.",
    },
    "reliability": {
        "impacto": "Riesgo de caídas del servicio, pérdida de datos y comportamiento inconsistente ante fallos del entorno o red.",
        "recomendacion": "Agregar escenarios de recuperación ante errores, reintentos automáticos y condiciones de fallo parcial.",
    },
    "security": {
        "impacto": "Exposición a accesos no autorizados, fuga de datos sensibles y vulnerabilidades explotables en producción.",
        "recomendacion": "Incluir pruebas de autenticación, autorización por rol, inyección, manejo de sesiones y datos sensibles.",
    },
    "maintainability": {
        "impacto": "Alta deuda técnica encubierta; cambios futuros podrían introducir regresiones no detectadas por falta de pruebas de regresión.",
        "recomendacion": "Asegurar cobertura de pruebas de regresión para módulos de alta complejidad ciclomática.",
    },
    "portability": {
        "impacto": "Riesgo de bloqueo tecnológico; la migración a nueva infraestructura o entorno podría ser costosa y propensa a errores.",
        "recomendacion": "Validar que el sistema puede desplegarse y operar correctamente en todos los entornos objetivo declarados.",
    },
}


def _nivel_riesgo(count: int, total: int) -> tuple[str, str]:
    """Clasifica el nivel de riesgo según cobertura. Retorna (etiqueta, color)."""
    if count == 0:
        return "Crítico", "#cf222e"
    pct = count / total if total else 0
    if pct < 0.05:
        return "Alto", "#bc4c00"
    if pct < 0.15:
        return "Medio", "#9a6700"
    return "Bajo", "#1a7f37"


def _e(text: str) -> str:
    """Escape HTML."""
    return html.escape(str(text), quote=True)


def _fmt_dt(dt_str: str | None) -> str:
    if not dt_str:
        return "—"
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except (ValueError, TypeError):
        return str(dt_str)


def _fmt_action(action: str) -> str:
    return {
        "accepted": "Aceptado",
        "reclassified": "Reclasificado",
        "comment_added": "Comentario",
        "approved": "Aprobado",
        "rejected": "Rechazado",
        "changes_requested": "Cambios solicitados",
    }.get(action, action)


# ============================================================
# SECCIONES HTML
# ============================================================
def _css() -> str:
    return """
    <style>
      *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

      body {
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 11pt;
        color: #1f2328;
        background: #f6f8fa;
      }

      .page {
        max-width: 900px;
        margin: 32px auto;
        background: #ffffff;
        border: 1px solid #d0d7de;
        border-radius: 6px;
        padding: 48px 56px;
      }

      /* ---- ENCABEZADO ---- */
      .header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        border-bottom: 3px solid #0550ae;
        padding-bottom: 20px;
        margin-bottom: 28px;
      }
      .header-brand { font-size: 22pt; font-weight: 700; color: #0550ae; }
      .header-sub   { font-size: 9pt; color: #6e7781; margin-top: 2px; }
      .header-meta  { text-align: right; font-size: 9pt; color: #6e7781; line-height: 1.6; }

      .doc-title {
        font-size: 17pt;
        font-weight: 700;
        color: #1f2328;
        margin-bottom: 4px;
      }
      .doc-subtitle { font-size: 10pt; color: #6e7781; margin-bottom: 20px; }

      /* ---- BADGE DE ESTADO ---- */
      .status-badge {
        display: inline-block;
        padding: 6px 18px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 11pt;
        color: #fff;
        margin-bottom: 28px;
      }

      /* ---- SECCIONES ---- */
      .section { margin-bottom: 36px; }
      .section-title {
        font-size: 12pt;
        font-weight: 700;
        color: #0550ae;
        border-bottom: 1px solid #d0d7de;
        padding-bottom: 6px;
        margin-bottom: 14px;
        text-transform: uppercase;
        letter-spacing: .5px;
      }
      .section-number {
        display: inline-block;
        background: #0550ae;
        color: #fff;
        font-size: 9pt;
        font-weight: 700;
        border-radius: 20px;
        min-width: 20px;
        height: 20px;
        text-align: center;
        line-height: 20px;
        padding: 0 5px;
        margin-right: 8px;
      }

      /* ---- INFO GRID ---- */
      .info-grid {
        display: grid;
        grid-template-columns: 200px 1fr;
        gap: 6px 16px;
        font-size: 10pt;
      }
      .info-label { color: #6e7781; font-weight: 600; }
      .info-value { color: #1f2328; }

      /* ---- RESUMEN CARDS ---- */
      .cards {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin-bottom: 16px;
      }
      .card {
        background: #f6f8fa;
        border: 1px solid #d0d7de;
        border-radius: 6px;
        padding: 14px 12px;
        text-align: center;
      }
      .card-num  { font-size: 22pt; font-weight: 700; color: #0550ae; }
      .card-lbl  { font-size: 8pt; color: #6e7781; text-transform: uppercase; letter-spacing: .5px; }

      /* ---- ISO TABLE ---- */
      .iso-table { width: 100%; border-collapse: collapse; font-size: 10pt; }
      .iso-table th {
        background: #0550ae;
        color: #fff;
        padding: 8px 10px;
        text-align: left;
        font-weight: 600;
      }
      .iso-table td { padding: 7px 10px; border-bottom: 1px solid #d0d7de; vertical-align: middle; }
      .iso-table tr:last-child td { border-bottom: none; }
      .iso-table tr:nth-child(even) td { background: #f6f8fa; }

      .bar-wrap { background: #e8edf2; border-radius: 4px; height: 12px; min-width: 120px; }
      .bar-fill  { background: #0550ae; height: 12px; border-radius: 4px; }

      /* ---- SCENARIO TABLE ---- */
      .scenario-table { width: 100%; border-collapse: collapse; font-size: 9.5pt; margin-bottom: 18px; }
      .scenario-table th {
        background: #2d333b;
        color: #cdd9e5;
        padding: 7px 8px;
        text-align: left;
        font-weight: 600;
      }
      .scenario-table td { padding: 6px 8px; border-bottom: 1px solid #d0d7de; vertical-align: top; }
      .scenario-table tr:last-child td { border-bottom: none; }
      .scenario-table tr:nth-child(even) td { background: #f6f8fa; }

      .feature-header {
        background: #ddf4ff;
        border: 1px solid #54aeff;
        border-radius: 4px;
        padding: 8px 12px;
        font-weight: 700;
        font-size: 10pt;
        color: #0550ae;
        margin: 16px 0 6px;
      }
      .feature-desc { font-size: 9pt; color: #6e7781; margin-bottom: 10px; }

      .type-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 8pt;
        font-weight: 600;
        color: #fff;
      }

      /* ---- COVERAGE MATRIX ---- */
      .matrix-table { width: 100%; border-collapse: collapse; font-size: 9.5pt; }
      .matrix-table th {
        background: #2d333b;
        color: #cdd9e5;
        padding: 7px 8px;
        text-align: left;
        font-weight: 600;
      }
      .matrix-table td { padding: 6px 8px; border-bottom: 1px solid #d0d7de; vertical-align: top; }
      .matrix-table tr:last-child td { border-bottom: none; }
      .matrix-table tr:nth-child(even) td { background: #f6f8fa; }

      /* ---- REQUIREMENTS TABLE ---- */
      .req-table { width: 100%; border-collapse: collapse; font-size: 10pt; margin-top: 16px; }
      .req-table th {
        background: #0550ae;
        color: #fff;
        padding: 8px 10px;
        text-align: left;
        font-weight: 600;
      }
      .req-table td { padding: 7px 10px; border-bottom: 1px solid #d0d7de; vertical-align: top; }
      .req-table tr:last-child td { border-bottom: none; }
      .req-table tr:nth-child(even) td { background: #f6f8fa; }

      /* ---- RISK TABLE ---- */
      .risk-table { width: 100%; border-collapse: collapse; font-size: 10pt; }
      .risk-table th {
        background: #2d333b;
        color: #cdd9e5;
        padding: 8px 10px;
        text-align: left;
        font-weight: 600;
      }
      .risk-table td { padding: 8px 10px; border-bottom: 1px solid #d0d7de; vertical-align: top; }
      .risk-table tr:last-child td { border-bottom: none; }
      .risk-table tr:nth-child(even) td { background: #f6f8fa; }

      .risk-badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 12px;
        font-size: 9pt;
        font-weight: 700;
        color: #fff;
      }
      .risk-legend {
        display: flex;
        gap: 16px;
        flex-wrap: wrap;
        font-size: 9pt;
        margin-bottom: 14px;
        padding: 10px 14px;
        background: #f6f8fa;
        border: 1px solid #d0d7de;
        border-radius: 6px;
      }
      .risk-legend-item { display: flex; align-items: center; gap: 6px; }

      /* ---- CHANGE HISTORY ---- */
      .history-table { width: 100%; border-collapse: collapse; font-size: 9pt; }
      .history-table th {
        background: #2d333b;
        color: #cdd9e5;
        padding: 7px 8px;
        font-weight: 600;
        text-align: left;
      }
      .history-table td { padding: 6px 8px; border-bottom: 1px solid #d0d7de; vertical-align: top; }
      .history-table tr:last-child td { border-bottom: none; }
      .history-table tr:nth-child(even) td { background: #f6f8fa; }

      /* ---- FIRMA ---- */
      .firma-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 40px;
        margin-top: 8px;
      }
      .firma-box {
        border: 1px solid #d0d7de;
        border-radius: 6px;
        padding: 20px 24px;
      }
      .firma-box-title { font-size: 10pt; font-weight: 700; color: #1f2328; margin-bottom: 16px; }
      .firma-line {
        border-top: 1px solid #1f2328;
        margin: 40px 0 6px;
      }
      .firma-campo { font-size: 9pt; color: #6e7781; margin-bottom: 10px; }
      .firma-campo span { display: block; font-weight: 600; color: #1f2328; }

      .footer {
        margin-top: 40px;
        padding-top: 16px;
        border-top: 1px solid #d0d7de;
        font-size: 8pt;
        color: #6e7781;
        text-align: center;
      }

      /* ---- PRINT ---- */
      @media print {
        body { background: #fff; }
        .page {
          max-width: 100%;
          margin: 0;
          border: none;
          border-radius: 0;
          padding: 20mm 18mm;
        }
        .section { page-break-inside: avoid; }
        .feature-header { page-break-before: auto; }
        .firma-grid { page-break-inside: avoid; }
      }
    </style>
"""


def _section(num: int, title: str, body: str) -> str:
    return f"""
    <div class="section">
      <div class="section-title">
        <span class="section-number">{num}</span>{_e(title)}
      </div>
      {body}
    </div>
"""


def _info_row(label: str, value: str) -> str:
    return f'<div class="info-label">{_e(label)}</div><div class="info-value">{value}</div>'


# ============================================================
# SECCIÓN REQUERIMIENTO Y ANÁLISIS
# ============================================================
def _section_req_analisis(contract_a) -> str:
    """Genera el cuerpo HTML de la sección 'Requerimiento y Análisis' a partir del Contract A."""
    if contract_a is None:
        return '<p style="font-size:10pt;color:#6e7781;font-style:italic;">Información del requerimiento original no disponible.</p>'

    # 4.1 Requerimiento original
    s41 = f"""
    <div style="margin-bottom:24px;">
      <div style="font-size:11pt;font-weight:600;color:#1f2328;margin-bottom:8px;">4.1 Requerimiento Original</div>
      <div style="background:#f6f8fa;border:1px solid #d0d7de;border-radius:6px;padding:14px 18px;
                  font-family:monospace;font-size:9.5pt;white-space:pre-wrap;color:#1f2328;line-height:1.6;">
{_e(contract_a.original_requirements_text)}
      </div>
    </div>
"""

    # 4.2 Ambigüedades resueltas
    all_ambiguities = [
        (story, ambi)
        for story in contract_a.user_stories
        for ambi in story.ambiguities_resolved
    ]

    if all_ambiguities:
        ambi_rows = ""
        for story, ambi in all_ambiguities:
            badge = (
                '<span style="background:#8250df;color:#fff;font-size:7.5pt;font-weight:700;'
                'padding:2px 8px;border-radius:10px;margin-left:8px;">Asumido por LLM</span>'
                if ambi.assumption_made else
                '<span style="background:#0550ae;color:#fff;font-size:7.5pt;font-weight:700;'
                'padding:2px 8px;border-radius:10px;margin-left:8px;">Resuelto por analista</span>'
            )
            ambi_rows += f"""
        <tr>
          <td style="font-size:9pt;color:#6e7781;white-space:nowrap;">{_e(story.id)}</td>
          <td style="font-size:9pt;">{_e(ambi.original_text)}</td>
          <td style="font-size:9pt;">{_e(ambi.resolution)}{badge}</td>
        </tr>
"""
        s42 = f"""
    <div style="margin-bottom:24px;">
      <div style="font-size:11pt;font-weight:600;color:#1f2328;margin-bottom:8px;">4.2 Ambigüedades Resueltas</div>
      <table class="iso-table">
        <thead>
          <tr>
            <th>Historia</th>
            <th>Texto ambiguo detectado</th>
            <th>Resolución aplicada</th>
          </tr>
        </thead>
        <tbody>{ambi_rows}</tbody>
      </table>
    </div>
"""
    else:
        s42 = """
    <div style="margin-bottom:24px;">
      <div style="font-size:11pt;font-weight:600;color:#1f2328;margin-bottom:8px;">4.2 Ambigüedades Resueltas</div>
      <p style="font-size:10pt;color:#6e7781;font-style:italic;">No se detectaron ambigüedades en este requerimiento.</p>
    </div>
"""

    # 4.3 Historias de usuario con criterios de aceptación
    _priority_colors = {"critical": "#cf222e", "high": "#bc4c00", "medium": "#9a6700", "low": "#1a7f37"}
    us_html = ""
    for story in contract_a.user_stories:
        priority_val = getattr(story.priority, "value", str(story.priority))
        priority_color = _priority_colors.get(priority_val.lower(), "#6e7781")

        ac_items = ""
        for ac in story.acceptance_criteria:
            neg_badge = (
                '<span style="background:#cf222e;color:#fff;font-size:7.5pt;font-weight:700;'
                'padding:2px 8px;border-radius:10px;margin-left:6px;">Caso negativo</span>'
                if ac.is_negative_case else ""
            )
            ac_items += f"""
          <div style="background:#f6f8fa;border:1px solid #d0d7de;border-radius:6px;padding:12px 14px;margin-bottom:8px;">
            <div style="font-size:10pt;font-weight:600;color:#1f2328;margin-bottom:8px;">
              {_e(ac.id)}{neg_badge}
              <span style="font-weight:400;color:#444d56;margin-left:8px;">{_e(ac.description)}</span>
            </div>
            <div style="display:grid;gap:6px;font-size:9.5pt;">
              <div style="padding:6px 10px;background:#ddf4ff;border-left:3px solid #0550ae;border-radius:0 4px 4px 0;">
                <strong style="color:#0550ae;">Dado que</strong> {_e(ac.given)}
              </div>
              <div style="padding:6px 10px;background:#fff8c5;border-left:3px solid #9a6700;border-radius:0 4px 4px 0;">
                <strong style="color:#9a6700;">Cuando</strong> {_e(ac.when)}
              </div>
              <div style="padding:6px 10px;background:#dafbe1;border-left:3px solid #1a7f37;border-radius:0 4px 4px 0;">
                <strong style="color:#1a7f37;">Entonces</strong> {_e(ac.then)}
              </div>
            </div>
          </div>
"""
        us_html += f"""
      <div style="border:1px solid #d0d7de;border-radius:6px;padding:16px 18px;margin-bottom:16px;">
        <div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:12px;">
          <span style="background:#0550ae;color:#fff;font-size:9pt;font-weight:700;
                       padding:3px 10px;border-radius:12px;white-space:nowrap;">{_e(story.id)}</span>
          <div style="flex:1;">
            <div style="font-size:11pt;font-weight:700;color:#1f2328;">{_e(story.title)}</div>
            <div style="font-size:9pt;color:#6e7781;margin-top:3px;">
              Como <strong>{_e(story.as_a)}</strong>,
              quiero <strong>{_e(story.i_want)}</strong>,
              para que <strong>{_e(story.so_that)}</strong>
            </div>
          </div>
          <span style="background:{priority_color};color:#fff;font-size:8pt;font-weight:700;
                       padding:2px 10px;border-radius:10px;white-space:nowrap;">{_e(priority_val.upper())}</span>
        </div>
        {ac_items}
      </div>
"""

    s43 = f"""
    <div>
      <div style="font-size:11pt;font-weight:600;color:#1f2328;margin-bottom:12px;">
        4.3 Historias de Usuario y Criterios de Aceptación
      </div>
      {us_html}
    </div>
"""

    return f"""
    <p style="font-size:10pt;color:#444d56;margin-bottom:16px;">
      Esta sección documenta el requerimiento original del cliente, las ambigüedades detectadas
      y resueltas durante el refinamiento (M1), y las historias de usuario con sus criterios de
      aceptación en formato Gherkin que sirvieron como base para la generación de los casos de prueba.
    </p>
    {s41}{s42}{s43}
"""


# ============================================================
# CONSTRUCCIÓN DEL ACTA
# ============================================================
def generar_acta_html(suite: GherkinTestSuite, original_path: Path, contract_a=None) -> str:
    rev = suite.review
    status_label, status_color = _STATUS_LABELS.get(
        rev.review_status, ("DESCONOCIDO", "#6e7781")
    )
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
    todos = [s for f in suite.features for s in f.scenarios]
    total = len(todos)
    max_cob = max(suite.coverage_by_characteristic.values(), default=1) or 1

    # ---- ENCABEZADO ----
    header = f"""
    <div class="header">
      <div>
        <div class="header-brand">QualityAI</div>
        <div class="header-sub">Pipeline de Automatización de Pruebas · Módulo 2</div>
      </div>
      <div class="header-meta">
        Documento: <strong>ACTA-{_e(suite.pipeline_run_id)}</strong><br>
        Emitido: {_e(ahora)}<br>
        Archivo origen: {_e(original_path.name)}
      </div>
    </div>
    <div class="doc-title">Acta de Aprobación del Plan de Pruebas de Software</div>
    <div class="doc-subtitle">
      Revisión formal de los casos de prueba realizada por el analista de calidad de software
    </div>
    <div class="status-badge" style="background:{status_color};">
      {_e(status_label)}
    </div>
    <div style="background:#f0f6ff;border:1px solid #b6d0f5;border-radius:6px;padding:14px 18px;margin-bottom:28px;font-size:10pt;color:#1f2328;line-height:1.6;">
      <strong>¿Qué es este documento?</strong><br>
      Este acta certifica que el plan de pruebas de software ha sido revisado y aprobado por el
      analista de calidad. Contiene el listado completo de casos de prueba diseñados para verificar
      que el sistema cumple con todos los requerimientos acordados, junto con el análisis de riesgos
      y la trazabilidad de cada requisito.<br><br>
      <strong>¿Por qué se solicita su firma?</strong><br>
      Su firma confirma que usted, como representante del cliente, ha revisado el alcance de las
      pruebas y está de acuerdo en que cubren adecuadamente los requerimientos del proyecto,
      autorizando así el avance a la siguiente etapa de desarrollo.
    </div>
"""

    # ---- S1: INFORMACIÓN DEL DOCUMENTO ----
    s1_body = f"""
    <p style="font-size:10pt;color:#444d56;margin-bottom:16px;">
      Este documento identifica el plan de pruebas evaluado y registra su estado oficial de aprobación.
      Sirve como referencia formal para el seguimiento y la trazabilidad del proceso de calidad.
    </p>
    <div class="info-grid">
      {_info_row("Identificador del acta", f'<span style="font-family:monospace;font-size:9.5pt;">{_e(suite.pipeline_run_id)}</span>')}
      {_info_row("Sistema generador de pruebas", _e(f"{suite.agent_name} v{suite.agent_version}"))}
      {_info_row("Fecha de generación del plan", _e(_fmt_dt(str(suite.created_at))))}
      {_info_row("Versión del plan de pruebas", f"<strong>{_e(str(rev.version))}</strong>")}
      {_info_row("Estado de aprobación", f'<strong style="color:{status_color};">{_e(status_label)}</strong>')}
      {_info_row("Requisitos sin casos de prueba", _e(", ".join(suite.uncovered_criteria) or "Ninguno — todos los requisitos tienen pruebas asignadas"))}
    </div>
"""

    # ---- S2: REVISOR Y DECISIÓN ----
    feedback_html = (
        f'<em>{_e(rev.analyst_feedback)}</em>'
        if rev.analyst_feedback
        else "<em style='color:#6e7781;'>(Sin observaciones adicionales)</em>"
    )
    s2_body = f"""
    <p style="font-size:10pt;color:#444d56;margin-bottom:16px;">
      El analista de calidad de software ha revisado el plan de pruebas y emitido la siguiente decisión
      basándose en la completitud y calidad de los casos de prueba definidos.
    </p>
    <div class="info-grid">
      {_info_row("Analista responsable", f"<strong>{_e(rev.approved_by or '—')}</strong>")}
      {_info_row("Fecha de la decisión", _e(_fmt_dt(str(rev.approved_at) if rev.approved_at else None)))}
      {_info_row("Decisión tomada", f'<strong style="color:{status_color};">{_e(status_label)}</strong>')}
      {_info_row("Observaciones del analista", feedback_html)}
    </div>
"""

    # ---- S3: RESUMEN EJECUTIVO ----
    edge = suite.total_scenarios - suite.total_positive - suite.total_negative - suite.total_boundary

    # Métricas por feature para el contexto de requerimientos
    us_ids = list(dict.fromkeys(f.user_story_id for f in suite.features))
    ac_ids = list(dict.fromkeys(cm.criterion_id for cm in suite.coverage_matrix))

    req_rows = ""
    for feature in suite.features:
        acs_feature = [
            cm.criterion_id for cm in suite.coverage_matrix
            if cm.user_story_id == feature.user_story_id
        ]
        req_rows += f"""
        <tr>
          <td style="font-size:9pt;color:#6e7781;white-space:nowrap;">{_e(feature.user_story_id)}</td>
          <td><strong>{_e(feature.name)}</strong></td>
          <td style="font-size:9pt;color:#444d56;">{_e(feature.description)}</td>
          <td style="text-align:center;">{len(acs_feature)}</td>
          <td style="text-align:center;">{len(feature.scenarios)}</td>
        </tr>
"""

    s3_body = f"""
    <p style="font-size:10pt;color:#444d56;margin-bottom:16px;">
      A continuación se presenta un resumen de los casos de prueba diseñados para validar los
      requerimientos del sistema. Cada <strong>caso de prueba</strong> simula una situación real
      de uso para verificar que el software responde correctamente.
    </p>
    <div class="cards">
      <div class="card">
        <div class="card-num">{total}</div>
        <div class="card-lbl">Casos de prueba totales</div>
      </div>
      <div class="card">
        <div class="card-num" style="color:#1a7f37;">{suite.total_positive}</div>
        <div class="card-lbl">Flujos exitosos</div>
      </div>
      <div class="card">
        <div class="card-num" style="color:#cf222e;">{suite.total_negative}</div>
        <div class="card-lbl">Casos de error</div>
      </div>
      <div class="card">
        <div class="card-num" style="color:#0550ae;">{suite.total_boundary}</div>
        <div class="card-lbl">Casos límite</div>
      </div>
    </div>
    <p style="font-size:9pt;color:#6e7781;margin-bottom:16px;">
      <strong>Flujos exitosos:</strong> pruebas donde el usuario realiza la acción correctamente. &nbsp;
      <strong>Casos de error:</strong> pruebas donde se verifica que el sistema maneja fallos o datos incorrectos. &nbsp;
      <strong>Casos límite:</strong> pruebas en valores extremos o justo en los bordes del rango permitido.
    </p>
    <div class="info-grid" style="margin-bottom:20px;">
      {_info_row("Funcionalidades principales evaluadas", str(len(us_ids)))}
      {_info_row("Requisitos verificados", str(len(ac_ids)))}
      {_info_row("Módulos evaluados", str(len(suite.features)))}
      {_info_row("Requisitos sin casos de prueba", _e(", ".join(suite.uncovered_criteria) or "Ninguno — cobertura completa"))}
      {_info_row("Casos especiales (extremos y manejo de errores)", str(max(0, edge)))}
    </div>
    <div style="font-size:10pt;font-weight:600;color:#1f2328;margin-bottom:8px;">
      Requerimientos evaluados por módulo
    </div>
    <p style="font-size:9pt;color:#6e7781;margin-bottom:10px;">
      La siguiente tabla muestra cada funcionalidad del sistema, su descripción y cuántos requisitos
      y casos de prueba le fueron asignados.
    </p>
    <table class="req-table">
      <thead>
        <tr>
          <th>Código</th>
          <th>Funcionalidad / Módulo</th>
          <th>Descripción del requerimiento</th>
          <th style="text-align:center;">Requisitos</th>
          <th style="text-align:center;">Casos de prueba</th>
        </tr>
      </thead>
      <tbody>{req_rows}</tbody>
    </table>
"""

    # ---- S4: COBERTURA ISO 25010 ----
    iso_rows = ""
    for qc in QualityCharacteristic:
        count = suite.coverage_by_characteristic.get(qc.value, 0)
        pct = int(count / max_cob * 100)
        label = _ISO_LABELS.get(qc.value, qc.value)
        desc = _ISO_DESCRIPTIONS.get(qc.value, "")
        iso_rows += f"""
        <tr>
          <td>
            <strong>{_e(label)}</strong><br>
            <small style="color:#6e7781;font-size:8.5pt;">{_e(desc)}</small>
          </td>
          <td style="text-align:center;">{count}</td>
          <td>
            <div class="bar-wrap">
              <div class="bar-fill" style="width:{pct}%;"></div>
            </div>
          </td>
        </tr>
"""
    s4_body = f"""
    <p style="font-size:10pt;color:#444d56;margin-bottom:16px;">
      Esta tabla muestra cuántos casos de prueba se diseñaron para verificar cada aspecto de calidad
      del sistema. La barra indica la cobertura relativa: a mayor longitud, más pruebas asignadas
      en ese aspecto.
    </p>
    <table class="iso-table">
      <thead>
        <tr>
          <th>Aspecto de calidad evaluado</th>
          <th style="text-align:center;">Casos de prueba</th>
          <th style="min-width:140px;">Cobertura relativa</th>
        </tr>
      </thead>
      <tbody>{iso_rows}</tbody>
    </table>
"""

    # ---- S5: CLASIFICACIÓN DE RIESGOS ----
    riesgo_rows = ""
    for qc in QualityCharacteristic:
        count = suite.coverage_by_characteristic.get(qc.value, 0)
        nivel, color = _nivel_riesgo(count, total)
        info = _ISO_RIESGOS.get(qc.value, {})
        label = _ISO_LABELS.get(qc.value, qc.value)
        pct_str = f"{count / total * 100:.1f}%" if total else "0.0%"
        riesgo_rows += f"""
        <tr>
          <td><strong>{_e(label)}</strong></td>
          <td style="text-align:center;">{count} <small style="color:#6e7781;">({pct_str})</small></td>
          <td style="text-align:center;">
            <span class="risk-badge" style="background:{color};">{_e(nivel)}</span>
          </td>
          <td style="font-size:9pt;">{_e(info.get('impacto', '—'))}</td>
          <td style="font-size:9pt;">{_e(info.get('recomendacion', '—'))}</td>
        </tr>
"""
    s5_riesgos_body = f"""
    <p style="font-size:10pt;color:#444d56;margin-bottom:16px;">
      Esta tabla identifica los aspectos del sistema que podrían representar un riesgo si no
      se prueban adecuadamente. A mayor nivel de riesgo, mayor es la probabilidad de que un
      fallo en esa área afecte al usuario final o al negocio.
    </p>
    <div class="risk-legend">
      <strong style="margin-right:4px;">Nivel de riesgo:</strong>
      <div class="risk-legend-item">
        <span class="risk-badge" style="background:#cf222e;">Crítico</span>
        Sin ningún caso de prueba asignado
      </div>
      <div class="risk-legend-item">
        <span class="risk-badge" style="background:#bc4c00;">Alto</span>
        Muy pocos casos de prueba (&lt; 5% del total)
      </div>
      <div class="risk-legend-item">
        <span class="risk-badge" style="background:#9a6700;">Medio</span>
        Cobertura parcial (5%–15% del total)
      </div>
      <div class="risk-legend-item">
        <span class="risk-badge" style="background:#1a7f37;">Bajo</span>
        Cobertura suficiente (&gt; 15% del total)
      </div>
    </div>
    <table class="risk-table">
      <thead>
        <tr>
          <th>Aspecto de calidad</th>
          <th style="text-align:center;">Casos de prueba</th>
          <th style="text-align:center;">Nivel de riesgo</th>
          <th>Consecuencia si no se cubre</th>
          <th>Acción recomendada</th>
        </tr>
      </thead>
      <tbody>{riesgo_rows}</tbody>
    </table>
"""

    # ---- S6 (antes S5): INVENTARIO DE ESCENARIOS ----
    inventario_html = f"""
    <p style="font-size:10pt;color:#444d56;margin-bottom:16px;">
      A continuación se listan todos los casos de prueba organizados por módulo o funcionalidad.
      Cada caso describe una situación concreta que se verificará durante la ejecución de las pruebas.
    </p>
"""
    for feature in suite.features:
        f_tags = " ".join(feature.tags) if feature.tags else ""
        inventario_html += f"""
        <div class="feature-header">
          Módulo: {_e(feature.name)}
          {f'&nbsp;<small style="font-weight:400;color:#6e7781;">{_e(f_tags)}</small>' if f_tags else ''}
          &nbsp;<small style="font-weight:400;color:#6e7781;">({len(feature.scenarios)} casos de prueba · Ref. {_e(feature.user_story_id)})</small>
        </div>
        <div class="feature-desc">{_e(feature.description)}</div>
        <table class="scenario-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Nombre del caso de prueba</th>
              <th>Tipo de prueba</th>
              <th>Aspecto de calidad</th>
              <th>Requisito</th>
              <th>Etiquetas</th>
            </tr>
          </thead>
          <tbody>
"""
        for i, sc in enumerate(feature.scenarios, 1):
            sc_color = _TYPE_COLORS.get(sc.scenario_type.value, "#6e7781")
            sc_type_label = _TYPE_LABELS.get(sc.scenario_type.value, sc.scenario_type.value)
            iso_label = _ISO_LABELS.get(sc.quality_characteristic.value, sc.quality_characteristic.value)
            tags_str = " ".join(sc.tags) if sc.tags else "—"
            inventario_html += f"""
            <tr>
              <td style="color:#6e7781;font-size:8pt;">{i}</td>
              <td>{_e(sc.name)}</td>
              <td>
                <span class="type-badge" style="background:{sc_color};">
                  {_e(sc_type_label)}
                </span>
              </td>
              <td style="font-size:9pt;">{_e(iso_label)}</td>
              <td style="font-size:9pt;color:#444d56;">{_e(sc.acceptance_criterion_id)}</td>
              <td style="font-size:8pt;color:#6e7781;">{_e(tags_str)}</td>
            </tr>
"""
        inventario_html += "</tbody></table>"

    # ---- S7 (antes S6): MATRIZ DE TRAZABILIDAD ----
    matrix_rows = ""
    for cm in suite.coverage_matrix:
        iso_cubiertos = ", ".join(
            _ISO_LABELS.get(qc.value, qc.value) for qc in cm.quality_characteristics_covered
        ) if cm.quality_characteristics_covered else "—"

        # Emparejar cada escenario con su tipo (listas paralelas 1:1)
        tipos = list(cm.coverage_type) if cm.coverage_type else []
        scenario_items = ""
        for idx, sc_name in enumerate(cm.scenario_names):
            if idx < len(tipos):
                tipo_val = tipos[idx].value
                tipo_label = (
                    tipo_val.replace("positive", "Flujo exitoso")
                             .replace("negative", "Caso de error")
                             .replace("boundary", "Caso límite")
                             .replace("edge_case", "Caso extremo")
                             .replace("error_handling", "Manejo de error")
                )
                tipo_color = _TYPE_COLORS.get(tipo_val, "#6e7781")
                badge = f'<span class="type-badge" style="background:{tipo_color};font-size:7.5pt;vertical-align:middle;">{_e(tipo_label)}</span>'
            else:
                badge = ""
            scenario_items += f'<div style="margin-bottom:5px;">{badge} {_e(sc_name)}</div>'

        matrix_rows += f"""
        <tr>
          <td style="font-size:9pt;color:#6e7781;white-space:nowrap;">{_e(cm.user_story_id)}</td>
          <td style="font-size:9pt;color:#444d56;white-space:nowrap;">{_e(cm.criterion_id)}</td>
          <td style="font-size:9pt;">{scenario_items}</td>
          <td style="font-size:9pt;">{_e(iso_cubiertos)}</td>
        </tr>
"""
    s6_body = f"""
    <p style="font-size:10pt;color:#444d56;margin-bottom:16px;">
      Esta tabla muestra la relación directa entre cada requisito del sistema y los casos de
      prueba diseñados para verificarlo. El tipo de prueba aparece junto a cada caso para indicar
      qué aspecto verifica (flujo exitoso, caso de error, caso límite, etc.).
    </p>
    <table class="matrix-table">
      <thead>
        <tr>
          <th>Funcionalidad</th>
          <th>Requisito verificado</th>
          <th>Casos de prueba (con su tipo)</th>
          <th>Aspectos de calidad cubiertos</th>
        </tr>
      </thead>
      <tbody>{matrix_rows}</tbody>
    </table>
"""

    # ---- S8 (antes S7): HISTORIAL DE REVISIÓN ----
    history_rows = ""
    for ch in rev.change_history:
        action_label = _fmt_action(ch.action)
        action_color = {
            "approved": "#1a7f37",
            "rejected": "#cf222e",
            "changes_requested": "#9a6700",
            "reclassified": "#0550ae",
        }.get(ch.action, "#6e7781")
        history_rows += f"""
        <tr>
          <td style="white-space:nowrap;font-size:8pt;">{_e(_fmt_dt(str(ch.timestamp)))}</td>
          <td><strong>{_e(ch.reviewer)}</strong></td>
          <td>
            <span style="color:{action_color};font-weight:600;">{_e(action_label)}</span>
          </td>
          <td style="font-size:9pt;">{_e(ch.notes or '—')}</td>
        </tr>
"""
    s7_body = f"""
    <p style="font-size:10pt;color:#444d56;margin-bottom:16px;">
      Registro cronológico de todas las acciones realizadas sobre este plan de pruebas.
      Este historial garantiza la trazabilidad del proceso de revisión y sirve como evidencia
      de auditoría del proceso de calidad.
    </p>
    <table class="history-table">
      <thead>
        <tr>
          <th>Fecha y hora</th>
          <th>Responsable</th>
          <th>Acción realizada</th>
          <th>Observaciones</th>
        </tr>
      </thead>
      <tbody>{history_rows}</tbody>
    </table>
"""

    # ---- S9 (antes S8): FIRMAS ----
    s8_body = f"""
    <div class="firma-grid">
      <div class="firma-box">
        <div class="firma-box-title">Analista de Calidad de Software — Responsable de la Revisión</div>
        <div class="firma-campo">
          Nombre:<br><span>{_e(rev.approved_by or '')}</span>
        </div>
        <div class="firma-campo">
          Fecha de aprobación:<br>
          <span>{_e(_fmt_dt(str(rev.approved_at) if rev.approved_at else None))}</span>
        </div>
        <div class="firma-line"></div>
        <div style="font-size:8pt;color:#6e7781;">Firma del Analista de QA</div>
      </div>
      <div class="firma-box">
        <div class="firma-box-title">Representante del Cliente</div>
        <div class="firma-campo">Nombre: <span>&nbsp;</span></div>
        <div class="firma-campo">Cargo: <span>&nbsp;</span></div>
        <div class="firma-campo">Empresa: <span>&nbsp;</span></div>
        <div class="firma-campo">Fecha: <span>&nbsp;</span></div>
        <div class="firma-line"></div>
        <div style="font-size:8pt;color:#6e7781;">Firma del Cliente / Representante Autorizado</div>
      </div>
    </div>
    <div style="margin-top:20px;font-size:9pt;color:#6e7781;background:#fffbdd;border:1px solid #e6c700;border-radius:6px;padding:14px 18px;">
      <strong>Nota importante:</strong> Al firmar este documento, el representante del cliente confirma
      que ha revisado y comprende el plan de pruebas descrito en las secciones anteriores, y otorga
      su conformidad formal para proceder con la siguiente etapa del proyecto.
      Este documento original firmado deberá conservarse como respaldo del proceso de aprobación.
    </div>
"""

    # ---- FOOTER ----
    footer = f"""
    <div class="footer">
      QualityAI · Pipeline M2 Test Architect · Pipeline Run: {_e(suite.pipeline_run_id)} ·
      Generado el {_e(ahora)} · Documento ACTA-{_e(suite.pipeline_run_id)}
    </div>
"""

    # ---- S4 (nueva): REQUERIMIENTO Y ANÁLISIS ----
    s4_req_body = _section_req_analisis(contract_a)

    # ---- ENSAMBLE ----
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Acta de Aprobación · {_e(suite.pipeline_run_id)}</title>
  {_css()}
</head>
<body>
  <div class="page">
    {header}
    {_section(1, "Identificación del Documento", s1_body)}
    {_section(2, "Responsable de Revisión y Decisión Tomada", s2_body)}
    {_section(3, "Resumen Ejecutivo y Contexto de Requerimientos", s3_body)}
    {_section(4, "Requerimiento y Análisis", s4_req_body)}
    {_section(5, "Cobertura de Aspectos de Calidad", s4_body)}
    {_section(6, "Análisis de Riesgos por Aspecto de Calidad", s5_riesgos_body)}
    {_section(7, "Catálogo de Casos de Prueba", inventario_html)}
    {_section(8, "Trazabilidad: Requisitos y Casos de Prueba", s6_body)}
    {_section(9, "Historial de Revisión y Auditoría", s7_body)}
    {_section(10, "Firmas", s8_body)}
    {footer}
  </div>
</body>
</html>
"""


# ============================================================
# PERSISTENCIA
# ============================================================
def guardar_acta(suite: GherkinTestSuite, original_path: Path, contract_a=None) -> Path:
    """Guarda el acta HTML junto al JSON revisado, con sufijo _acta.html."""
    stem = original_path.stem
    if stem.endswith("_reviewed"):
        base = stem[: -len("_reviewed")]
    else:
        base = stem
    output_path = original_path.with_name(f"{base}_acta.html")
    html_content = generar_acta_html(suite, original_path, contract_a)
    output_path.write_text(html_content, encoding="utf-8")
    return output_path


# ============================================================
# EJECUCIÓN
# ============================================================
if __name__ == "__main__":
    print()
    print("QualityAI — Generador de Acta de Aprobación (HTML)")
    print()

    if len(sys.argv) > 1:
        contract_b_path = Path(sys.argv[1])
    else:
        output_dir = Path(__file__).parent / "output"
        if not output_dir.exists():
            print(f"Error: directorio {output_dir} no existe.")
            sys.exit(1)

        archivos = sorted(output_dir.glob("contract_b_*_reviewed.json"))
        if not archivos:
            archivos = sorted(output_dir.glob("contract_b_*.json"))

        if not archivos:
            print(f"Error: no hay archivos contract_b_*.json en {output_dir}")
            sys.exit(1)

        print("Contract B disponibles:")
        for i, f in enumerate(archivos, 1):
            print(f"   {i}) {f.name}")
        try:
            elec = input("\nNúmero del archivo: ").strip()
            contract_b_path = archivos[int(elec) - 1]
        except (ValueError, IndexError, EOFError, KeyboardInterrupt):
            print("\nElección inválida.")
            sys.exit(1)

    if not contract_b_path.exists():
        print(f"Error: archivo no encontrado: {contract_b_path}")
        sys.exit(1)

    print(f"\nCargando: {contract_b_path.name}")
    with open(contract_b_path, encoding="utf-8") as f:
        data = json.load(f)
    suite = GherkinTestSuite(**data)

    rev = suite.review
    status_label, _ = _STATUS_LABELS.get(rev.review_status, ("DESCONOCIDO", ""))
    print(f"   Estado: {status_label}")
    print(f"   Revisor: {rev.approved_by or '(no asignado)'}")
    print(f"   Escenarios: {suite.total_scenarios}")

    if rev.review_status == "pending_review":
        print("\nAdvertencia: el suite aún está en pending_review.")
        print("Se generará el acta igualmente, pero no tendrá firma del analista.")

    output_path = guardar_acta(suite, contract_b_path)
    print(f"\nActa generada: {output_path}")
    print("Abre el archivo en un navegador e imprime con Ctrl+P para obtener el PDF.")
