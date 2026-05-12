import { useState } from 'react'

const QC_OPTIONS = [
  { value: 'functional_suitability', label: 'Idoneidad Funcional' },
  { value: 'performance_efficiency', label: 'Eficiencia de Desempeño' },
  { value: 'compatibility', label: 'Compatibilidad' },
  { value: 'usability', label: 'Usabilidad' },
  { value: 'reliability', label: 'Fiabilidad' },
  { value: 'security', label: 'Seguridad' },
  { value: 'maintainability', label: 'Mantenibilidad' },
  { value: 'portability', label: 'Portabilidad' },
]

const TYPE_COLORS = {
  positive: 'bg-green-100 text-green-700',
  negative: 'bg-red-100 text-red-700',
  boundary: 'bg-amber-100 text-amber-700',
  edge_case: 'bg-orange-100 text-orange-700',
  error_handling: 'bg-purple-100 text-purple-700',
}

const ACTIONS = [
  { value: 'accept', label: 'Aceptar', icon: '✓', color: 'bg-green-600 hover:bg-green-700 text-white' },
  { value: 'reclassify', label: 'Reclasificar', icon: '↺', color: 'bg-amber-500 hover:bg-amber-600 text-white' },
  { value: 'comment', label: 'Comentar', icon: '✎', color: 'bg-blue-500 hover:bg-blue-600 text-white' },
  { value: 'skip', label: 'Saltar', icon: '→', color: 'bg-slate-200 hover:bg-slate-300 text-slate-700' },
]

export default function ScenarioReviewCard({ scenario, index, total, onAction }) {
  const [action, setAction] = useState('accept')
  const [newQC, setNewQC] = useState(scenario.quality_characteristic)
  const [note, setNote] = useState('')

  const canSubmit =
    action !== 'reclassify' ||
    (newQC !== scenario.quality_characteristic)

  function handleSubmit() {
    const opts = {}
    if (action === 'reclassify') {
      opts.new_quality_characteristic = newQC
      opts.note = note || undefined
    } else if (action === 'comment') {
      opts.note = note || undefined
    }
    onAction(action, opts)
    setAction('accept')
    setNote('')
  }

  const progress = Math.round(((index + 1) / total) * 100)

  return (
    <div className="space-y-4">
      {/* Barra de progreso */}
      <div className="flex items-center gap-3">
        <span className="text-xs text-slate-400 shrink-0">
          Escenario {index + 1} de {total}
        </span>
        <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-indigo-500 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="text-xs font-medium text-indigo-600 shrink-0">{progress}%</span>
      </div>

      {/* Tarjeta del escenario */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 space-y-4">
        <div className="flex items-start justify-between gap-3">
          <h3 className="font-semibold text-slate-800 text-sm leading-snug flex-1">
            {scenario.name}
          </h3>
          <span className={`shrink-0 text-xs px-2.5 py-0.5 rounded-full font-medium ${TYPE_COLORS[scenario.scenario_type] || 'bg-slate-100 text-slate-600'}`}>
            {scenario.scenario_type}
          </span>
        </div>

        <div className="flex flex-wrap gap-1.5">
          <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 font-medium">
            ISO: {scenario.quality_characteristic.replace(/_/g, ' ')}
          </span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-500">
            {scenario.acceptance_criterion_id}
          </span>
          {(scenario.tags || []).slice(0, 4).map(t => (
            <span key={t} className="text-xs px-2 py-0.5 rounded-full bg-slate-50 text-slate-400 border border-slate-100">
              {t}
            </span>
          ))}
        </div>

        {/* Pasos Gherkin */}
        <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-100 space-y-1">
          {(scenario.steps || []).map((step, i) => (
            <div key={i} className="flex gap-2 text-xs font-mono">
              <span className="text-indigo-500 font-bold w-10 shrink-0">{step.keyword}</span>
              <span className="text-slate-700">{step.text}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Panel de acciones */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-4 space-y-3">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Acción</p>

        <div className="flex flex-wrap gap-2">
          {ACTIONS.map(a => (
            <button
              key={a.value}
              onClick={() => setAction(a.value)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium transition border-2 ${
                action === a.value
                  ? `${a.color} border-transparent`
                  : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300'
              }`}
            >
              <span>{a.icon}</span>
              <span>{a.label}</span>
            </button>
          ))}
        </div>

        {action === 'reclassify' && (
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-600">Nueva clasificación ISO 25010</label>
            <select
              value={newQC}
              onChange={e => setNewQC(e.target.value)}
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
            >
              {QC_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            <input
              value={note}
              onChange={e => setNote(e.target.value)}
              placeholder="Razón del cambio (recomendado)..."
              className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        )}

        {action === 'comment' && (
          <input
            value={note}
            onChange={e => setNote(e.target.value)}
            placeholder="Escribe tu comentario..."
            className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        )}

        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="w-full py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-semibold disabled:opacity-40 hover:bg-indigo-700 transition"
        >
          Confirmar →
        </button>
      </div>
    </div>
  )
}
