import { useEffect, useState } from 'react'
import HITLReview from './HITLReview'
import GlobalDecisionForm from './pipeline/GlobalDecisionForm'
import ScenarioReviewCard from './pipeline/ScenarioReviewCard'
import { usePipelineWebSocket } from '../hooks/usePipelineWebSocket'

// ── Sub-componentes internos ─────────────────────────────────────────────────

function ProgressPanel({ statusMessage, pipelineState, m2Progress }) {
  const isM2 = pipelineState === 'm2_generating'
  const pct = isM2 && m2Progress.total > 0
    ? Math.round((m2Progress.done / m2Progress.total) * 100)
    : null

  return (
    <div className="flex flex-col items-center justify-center py-28 gap-6">
      <div className="relative w-16 h-16">
        <div className="absolute inset-0 rounded-full border-4 border-indigo-100" />
        <div className="absolute inset-0 rounded-full border-4 border-indigo-600 border-t-transparent animate-spin" />
      </div>
      <div className="text-center space-y-1">
        <p className="text-slate-700 font-medium">{statusMessage || 'Procesando...'}</p>
        {isM2 && m2Progress.total > 0 && (
          <div className="mt-3 w-64 space-y-1">
            <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-indigo-500 rounded-full transition-all duration-500"
                style={{ width: `${pct}%` }}
              />
            </div>
            <p className="text-xs text-slate-400">
              {m2Progress.done} / {m2Progress.total} criterios de aceptación
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

function ReviewerIdPanel({ totalScenarios, onSubmit }) {
  const [reviewerId, setReviewerId] = useState('')
  return (
    <div className="space-y-6">
      <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-5 flex items-start gap-3">
        <span className="text-2xl shrink-0">✅</span>
        <div>
          <p className="font-semibold text-emerald-800 text-sm">Generación completada</p>
          <p className="text-emerald-700 text-xs mt-0.5">
            {totalScenarios} escenario{totalScenarios !== 1 ? 's' : ''} Gherkin listos para revisión
          </p>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 space-y-4">
        <div>
          <h3 className="font-semibold text-slate-800">Identificación del revisor</h3>
          <p className="text-slate-500 text-xs mt-1">
            Tu identidad quedará registrada en el historial de revisión del Contract B.
          </p>
        </div>
        <input
          value={reviewerId}
          onChange={e => setReviewerId(e.target.value)}
          placeholder="ej: ana.garcia"
          className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          onKeyDown={e => { if (e.key === 'Enter' && reviewerId.trim()) onSubmit(reviewerId.trim()) }}
        />
        <button
          onClick={() => onSubmit(reviewerId.trim())}
          disabled={!reviewerId.trim()}
          className="w-full py-3 rounded-xl bg-indigo-600 text-white font-semibold text-sm disabled:opacity-40 hover:bg-indigo-700 transition"
        >
          Iniciar revisión de escenarios →
        </button>
      </div>
    </div>
  )
}

function CompletedView({ result, onBack }) {
  const { status, total_scenarios, acta_html } = result

  const STATUS_CONFIG = {
    approved: { label: 'APROBADO', color: 'text-green-700 bg-green-50 border-green-200', icon: '✅' },
    rejected: { label: 'RECHAZADO', color: 'text-red-700 bg-red-50 border-red-200', icon: '❌' },
    needs_changes: { label: 'CAMBIOS REQUERIDOS', color: 'text-amber-700 bg-amber-50 border-amber-200', icon: '🔄' },
  }
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.rejected

  function downloadActa() {
    const blob = new Blob([acta_html], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `acta_aprobacion_${new Date().toISOString().slice(0, 10)}.html`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      <div className={`rounded-2xl border p-6 flex items-center gap-4 ${cfg.color}`}>
        <span className="text-4xl">{cfg.icon}</span>
        <div>
          <p className="font-bold text-lg">{cfg.label}</p>
          <p className="text-sm mt-0.5 opacity-80">
            Suite con {total_scenarios} escenario{total_scenarios !== 1 ? 's' : ''} · Pipeline M1+M2 completado
          </p>
        </div>
      </div>

      {acta_html && (
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 space-y-3">
          <h3 className="font-semibold text-slate-800 text-sm">Acta de Aprobación</h3>
          <p className="text-slate-500 text-xs">
            El acta está lista. Descárgala y ábrela en el navegador para imprimirla como PDF (Ctrl+P).
          </p>
          <button
            onClick={downloadActa}
            className="w-full py-3 rounded-xl bg-emerald-600 text-white font-semibold text-sm hover:bg-emerald-700 transition flex items-center justify-center gap-2"
          >
            <span>⬇</span>
            <span>Descargar Acta HTML</span>
          </button>
        </div>
      )}

      <button
        onClick={onBack}
        className="w-full py-2.5 rounded-xl border border-slate-200 text-slate-600 text-sm font-medium hover:bg-slate-50 transition"
      >
        ← Nueva consulta
      </button>
    </div>
  )
}

function ErrorPanel({ message, onBack }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-2xl p-10 text-center space-y-4">
      <div className="text-4xl">⚠️</div>
      <div>
        <p className="text-red-700 font-semibold text-lg">Error en el pipeline</p>
        <p className="text-red-500 text-sm mt-1 max-w-md mx-auto">{message}</p>
      </div>
      <button
        onClick={onBack}
        className="px-6 py-2.5 bg-red-600 text-white rounded-xl hover:bg-red-700 text-sm font-medium transition"
      >
        Volver al inicio
      </button>
    </div>
  )
}

// ── Componente principal ─────────────────────────────────────────────────────

export default function PipelineView({ requirement, topK, interactiveM1 = true, onBack }) {
  const {
    state,
    startPipeline,
    resolveAmbiguities,
    sendReviewerId,
    submitScenarioAction,
    submitGlobalDecision,
  } = usePipelineWebSocket()

  const {
    pipelineState, statusMessage, ambiguities, m2Progress,
    totalScenarios, currentScenario, coverageComparison, pipelineResult, error,
  } = state

  useEffect(() => {
    // startPipeline devuelve un cancelador del setTimeout interno.
    // Devolverlo aquí garantiza que React StrictMode cancele el timer
    // antes del re-mount, evitando que se envíen dos 'start_pipeline'
    // sobre la misma conexión WebSocket.
    const cancel = startPipeline(requirement, topK, interactiveM1)
    return typeof cancel === 'function' ? cancel : undefined
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // ── Renderizado según estado ─────────────────────────────────────────────

  if (pipelineState === 'error') {
    return <ErrorPanel message={error} onBack={onBack} />
  }

  if (['idle', 'connecting', 'm1_running', 'm2_generating', 'saving'].includes(pipelineState)) {
    return (
      <ProgressPanel
        statusMessage={statusMessage}
        pipelineState={pipelineState}
        m2Progress={m2Progress}
      />
    )
  }

  if (pipelineState === 'm1_waiting_resolutions') {
    const hitlData = {
      ambiguities,
      requires_review: ambiguities.length > 0,
      session_id: null,
      requirement_preview: requirement.slice(0, 100) + (requirement.length > 100 ? '...' : ''),
    }
    return (
      <HITLReview
        hitlData={hitlData}
        onSubmit={resolveAmbiguities}
        onCancel={onBack}
      />
    )
  }

  if (pipelineState === 'm2_waiting_reviewer_id' || pipelineState === 'm2_completed') {
    return (
      <ReviewerIdPanel
        totalScenarios={totalScenarios}
        onSubmit={sendReviewerId}
      />
    )
  }

  if (pipelineState === 'm2_reviewing' && currentScenario) {
    return (
      <ScenarioReviewCard
        scenario={currentScenario.scenario}
        index={currentScenario.index}
        total={currentScenario.total}
        onAction={(action, opts) => submitScenarioAction(currentScenario.index, action, opts)}
      />
    )
  }

  if (pipelineState === 'm2_waiting_global' && coverageComparison) {
    return (
      <GlobalDecisionForm
        coverageComparison={coverageComparison}
        onDecide={submitGlobalDecision}
      />
    )
  }

  if (pipelineState === 'completed' && pipelineResult) {
    return <CompletedView result={pipelineResult} onBack={onBack} />
  }

  return null
}
