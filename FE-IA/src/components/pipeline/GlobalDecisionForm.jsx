import { useState } from 'react'

const QC_LABELS = {
  functional_suitability: 'Idoneidad Funcional',
  performance_efficiency: 'Eficiencia',
  compatibility: 'Compatibilidad',
  usability: 'Usabilidad',
  reliability: 'Fiabilidad',
  security: 'Seguridad',
  maintainability: 'Mantenibilidad',
  portability: 'Portabilidad',
}

const DECISIONS = [
  {
    value: 'approve',
    label: 'APROBAR',
    icon: '✓',
    activeClass: 'bg-green-600 text-white border-green-600',
    hoverClass: 'hover:border-green-400 hover:text-green-700',
  },
  {
    value: 'request_changes',
    label: 'PEDIR CAMBIOS',
    icon: '↺',
    activeClass: 'bg-amber-500 text-white border-amber-500',
    hoverClass: 'hover:border-amber-400 hover:text-amber-700',
  },
  {
    value: 'reject',
    label: 'RECHAZAR',
    icon: '✕',
    activeClass: 'bg-red-600 text-white border-red-600',
    hoverClass: 'hover:border-red-400 hover:text-red-700',
  },
]

export default function GlobalDecisionForm({ coverageComparison, onDecide }) {
  const [decision, setDecision] = useState(null)
  const [feedback, setFeedback] = useState('')

  const { reclassifications, before, after } = coverageComparison

  function handleSubmit() {
    if (!decision) return
    onDecide(decision, feedback)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-800">Decisión global del suite</h2>
        <p className="text-slate-500 text-sm mt-1">
          Revisión completada · {reclassifications} reclasificación{reclassifications !== 1 ? 'es' : ''}
        </p>
      </div>

      {/* Tabla de cobertura */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
        <div className="px-5 py-3 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-700">Cobertura ISO 25010 — antes vs después</h3>
          {reclassifications > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 font-medium">
              {reclassifications} cambio{reclassifications !== 1 ? 's' : ''}
            </span>
          )}
        </div>
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-slate-800 text-slate-200">
              <th className="px-4 py-2.5 text-left font-medium">Característica</th>
              <th className="px-3 py-2.5 text-center font-medium w-16">Antes</th>
              <th className="px-3 py-2.5 text-center font-medium w-16">Después</th>
              <th className="px-3 py-2.5 text-center font-medium w-16">Delta</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(QC_LABELS).map(([qc, label]) => {
              const a = (before || {})[qc] ?? 0
              const d = (after || {})[qc] ?? 0
              const delta = d - a
              return (
                <tr key={qc} className="border-b border-slate-50 hover:bg-slate-50 transition">
                  <td className="px-4 py-2 text-slate-700">{label}</td>
                  <td className="px-3 py-2 text-center text-slate-400">{a}</td>
                  <td className="px-3 py-2 text-center font-semibold text-slate-700">{d}</td>
                  <td className={`px-3 py-2 text-center font-bold ${
                    delta > 0 ? 'text-green-600' : delta < 0 ? 'text-red-500' : 'text-slate-300'
                  }`}>
                    {delta > 0 ? `+${delta}` : delta === 0 ? '—' : delta}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Botones de decisión */}
      <div className="flex gap-3">
        {DECISIONS.map(d => (
          <button
            key={d.value}
            onClick={() => setDecision(d.value)}
            className={`flex-1 py-3 rounded-xl text-sm font-bold border-2 transition flex items-center justify-center gap-1.5
              ${decision === d.value
                ? d.activeClass
                : `bg-white text-slate-600 border-slate-200 ${d.hoverClass}`
              }`}
          >
            <span>{d.icon}</span>
            <span>{d.label}</span>
          </button>
        ))}
      </div>

      {/* Feedback opcional */}
      <div className="space-y-1.5">
        <label className="text-xs font-semibold text-slate-500">Comentario libre (opcional)</label>
        <textarea
          value={feedback}
          onChange={e => setFeedback(e.target.value)}
          placeholder="Observaciones para el equipo de desarrollo..."
          rows={3}
          className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
        />
      </div>

      <button
        onClick={handleSubmit}
        disabled={!decision}
        className="w-full py-3.5 rounded-xl bg-indigo-600 text-white text-sm font-bold disabled:opacity-40 hover:bg-indigo-700 transition shadow-sm"
      >
        Confirmar decisión final
      </button>
    </div>
  )
}
