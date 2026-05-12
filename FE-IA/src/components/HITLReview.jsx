import { useState, useMemo } from 'react'

const SEVERITY = {
  alta: {
    bg: 'bg-red-50',
    border: 'border-red-200',
    badge: 'bg-red-100 text-red-700',
    dot: 'bg-red-500',
    label: 'Alta',
  },
  media: {
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    badge: 'bg-amber-100 text-amber-700',
    dot: 'bg-amber-500',
    label: 'Media',
  },
  baja: {
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    badge: 'bg-emerald-100 text-emerald-700',
    dot: 'bg-emerald-500',
    label: 'Baja',
  },
}

const ACTIONS = [
  { value: 'accept', label: 'Aceptar sugerencia', icon: '✅' },
  { value: 'custom', label: 'Mi resolución', icon: '✏️' },
  { value: 'dismiss', label: 'No es ambiguo', icon: '⏭️' },
]

export default function HITLReview({ hitlData, onSubmit, onCancel }) {
  // Agrupar por palabra única (deduplicar contextos)
  const grouped = useMemo(() => {
    const map = {}
    for (const amb of hitlData.ambiguities) {
      if (!map[amb.word]) {
        map[amb.word] = { ...amb, contexts: [] }
      }
      map[amb.word].contexts.push(amb.context)
    }
    return Object.values(map)
  }, [hitlData.ambiguities])

  const [choices, setChoices] = useState(() =>
    grouped.map(g => ({
      word: g.word,
      category: g.category,
      action: 'accept',
      custom_text: '',
    }))
  )

  const updateChoice = (index, patch) =>
    setChoices(prev => prev.map((c, i) => (i === index ? { ...c, ...patch } : c)))

  const canSubmit = choices.every(
    c => c.action !== 'custom' || c.custom_text.trim().length > 0
  )

  const resolvedCount = choices.filter(c => c.action !== 'dismiss').length
  const dismissedCount = choices.filter(c => c.action === 'dismiss').length

  function handleSubmit() {
    const resolutions = choices.map((c, i) => ({
      word: c.word,
      category: c.category,
      analyst_resolution:
        c.action === 'accept'
          ? grouped[i].suggestion
          : c.action === 'custom'
          ? c.custom_text
          : '',
      status: c.action === 'dismiss' ? 'dismissed' : 'resolved',
    }))
    onSubmit(resolutions)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start gap-4">
        <div className="flex-1">
          <h2 className="text-2xl font-bold text-slate-800 tracking-tight">Revisión de ambigüedades</h2>
          <p className="text-slate-500 text-sm mt-1">
            Se detectaron{' '}
            <span className="font-semibold text-indigo-600">{grouped.length}</span>{' '}
            {grouped.length === 1 ? 'ambigüedad' : 'ambigüedades'} en tu requerimiento.
            Resuélvelas antes de continuar.
          </p>
        </div>
        <button
          onClick={onCancel}
          className="shrink-0 text-slate-400 hover:text-slate-600 transition text-sm px-3 py-1.5 rounded-lg hover:bg-slate-100"
        >
          ✕ Cancelar
        </button>
      </div>

      {/* Requirement preview */}
      <div className="bg-white border border-slate-100 rounded-xl px-5 py-4 shadow-sm">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1">Requerimiento analizado</p>
        <p className="text-sm text-slate-700 leading-relaxed">{hitlData.requirement_preview}</p>
      </div>

      {/* Severity legend */}
      <div className="flex items-center gap-1 text-xs text-slate-500 flex-wrap">
        <span className="mr-1">Severidad:</span>
        {Object.entries(SEVERITY).map(([key, cfg]) => (
          <span key={key} className={`flex items-center gap-1 px-2 py-0.5 rounded-full ${cfg.badge}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
            {cfg.label}
          </span>
        ))}
      </div>

      {/* Ambiguity cards */}
      <div className="space-y-4">
        {grouped.map((amb, i) => {
          const sev = SEVERITY[amb.severity] ?? SEVERITY.baja
          const choice = choices[i]

          return (
            <div
              key={`${amb.word}-${i}`}
              className={`rounded-2xl border p-5 space-y-4 transition ${sev.bg} ${sev.border}`}
            >
              {/* Card header */}
              <div className="flex items-center gap-2 flex-wrap justify-between">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold ${sev.badge}`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${sev.dot}`} />
                    {sev.label}
                  </span>
                  <code className="text-sm font-bold text-slate-800 bg-white/80 px-2.5 py-0.5 rounded-lg border border-white/50">
                    "{amb.word}"
                  </code>
                  <span className="text-xs text-slate-500 bg-white/60 px-2 py-0.5 rounded-lg">
                    {amb.category.replace(/_/g, ' ')}
                  </span>
                </div>
                <span className="text-xs text-slate-400">
                  IEEE 830: <em>{amb.ieee_830_violation}</em>
                </span>
              </div>

              {/* Contexts (can be multiple if word appears twice) */}
              <div className="space-y-1">
                {amb.contexts.map((ctx, ci) => (
                  <p
                    key={ci}
                    className="text-xs text-slate-500 font-mono bg-white/70 rounded-lg px-3 py-2 leading-relaxed border border-white/50"
                  >
                    {ctx}
                  </p>
                ))}
              </div>

              {/* Suggestion */}
              <div className="flex items-start gap-2 text-xs text-slate-600">
                <span className="shrink-0 text-base leading-none">💡</span>
                <div>
                  <span className="font-semibold text-slate-500">Sugerencia: </span>
                  {amb.suggestion}
                </div>
              </div>

              {/* Action selector */}
              <div className="space-y-2.5">
                <p className="text-xs font-semibold text-slate-600">¿Qué deseas hacer?</p>
                <div className="flex flex-wrap gap-2">
                  {ACTIONS.map(opt => (
                    <button
                      key={opt.value}
                      onClick={() => updateChoice(i, { action: opt.value })}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium transition border ${
                        choice.action === opt.value
                          ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm'
                          : 'bg-white/80 text-slate-600 border-slate-200 hover:border-indigo-300 hover:text-indigo-600'
                      }`}
                    >
                      <span>{opt.icon}</span>
                      {opt.label}
                    </button>
                  ))}
                </div>

                {/* Custom text input */}
                {choice.action === 'custom' && (
                  <div className="space-y-1">
                    <input
                      type="text"
                      value={choice.custom_text}
                      onChange={e => updateChoice(i, { custom_text: e.target.value })}
                      placeholder={`Escribe tu resolución para "${amb.word}"...`}
                      className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition"
                      autoFocus
                    />
                    {choice.custom_text.trim().length === 0 && (
                      <p className="text-xs text-red-400">La resolución no puede estar vacía.</p>
                    )}
                  </div>
                )}

                {/* Accept preview */}
                {choice.action === 'accept' && (
                  <p className="text-xs text-slate-500 bg-white/60 rounded-lg px-3 py-2 italic">
                    Se usará: "{amb.suggestion}"
                  </p>
                )}

                {/* Dismiss note */}
                {choice.action === 'dismiss' && (
                  <p className="text-xs text-slate-400 italic">
                    Esta ambigüedad será ignorada y el LLM no recibirá instrucciones sobre ella.
                  </p>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Summary + submit */}
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-5 space-y-4">
        <div className="flex items-center gap-4 text-xs text-slate-500">
          <span className="flex items-center gap-1">
            <span className="text-green-500">✅</span>
            <span className="font-medium text-slate-700">{resolvedCount}</span> resueltas
          </span>
          <span className="flex items-center gap-1">
            <span>⏭️</span>
            <span className="font-medium text-slate-700">{dismissedCount}</span> descartadas
          </span>
        </div>

        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="px-5 py-2.5 rounded-xl border border-slate-200 text-slate-600 text-sm font-medium hover:bg-slate-50 transition"
          >
            Cancelar
          </button>
          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="flex-1 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 active:bg-indigo-800 disabled:opacity-40 disabled:cursor-not-allowed transition shadow-sm"
          >
            Generar requerimiento refinado →
          </button>
        </div>
      </div>
    </div>
  )
}
