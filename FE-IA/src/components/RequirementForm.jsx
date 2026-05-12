const AGENTS = [
  {
    value: '1',
    label: 'Agente 1 — RAG Básico',
    desc: 'RAG + texto libre. Sin estructura JSON. Ideal para exploración rápida.',
    badge: 'Texto',
    badgeColor: 'bg-slate-100 text-slate-600',
    icon: '📄',
  },
  {
    value: '2',
    label: 'Agente 2 — RAG + JSON',
    desc: 'RAG + salida JSON estructurada y validada contra Contract A.',
    badge: 'JSON',
    badgeColor: 'bg-blue-100 text-blue-700',
    icon: '🗂️',
  },
  {
    value: '3',
    label: 'Agente 3 — RAG + Ambigüedades',
    desc: 'RAG + JSON + detección y resolución automática de ambigüedades con el LLM.',
    badge: 'Auto',
    badgeColor: 'bg-indigo-100 text-indigo-700',
    icon: '🔍',
  },
  {
    value: '4',
    label: 'Agente 4 — HITL Interactivo',
    desc: 'RAG + JSON + revisión manual de ambigüedades con el analista antes de generar el resultado.',
    badge: 'HITL',
    badgeColor: 'bg-purple-100 text-purple-700',
    icon: '🧑‍💻',
  },
  {
    value: '5',
    label: 'Agente 5 — Pipeline M1+M2 Completo',
    desc: 'Pipeline interactivo completo: refinamiento HITL (M1) + generación de escenarios Gherkin con ISO 25010 + revisión analista (M2) + Acta de Aprobación HTML.',
    badge: 'Full',
    badgeColor: 'bg-emerald-100 text-emerald-700',
    icon: '🔬',
  },
]

export default function RequirementForm({
  requirement, setRequirement,
  agent, setAgent,
  topK, setTopK,
  onSubmit,
}) {
  const selected = AGENTS.find(a => a.value === agent)
  const isValid = requirement.trim().length >= 10

  return (
    <div className="space-y-8">
      {/* Page title */}
      <div>
        <h2 className="text-3xl font-bold text-slate-800 tracking-tight">Analizar requerimiento</h2>
        <p className="text-slate-500 text-sm mt-2">
          Describe el requerimiento en lenguaje natural y selecciona el agente que lo procesará.
        </p>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-8 space-y-7">

        {/* Requirement textarea */}
        <div className="space-y-2">
          <label className="block text-sm font-semibold text-slate-700">
            Requerimiento <span className="text-red-400">*</span>
          </label>
          <textarea
            value={requirement}
            onChange={e => setRequirement(e.target.value)}
            placeholder="Ej: El sistema debe gestionar usuarios de forma segura y eficiente, permitiendo el registro, autenticación y recuperación de contraseña..."
            rows={5}
            className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-800 placeholder-slate-400 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition leading-relaxed"
          />
          <div className="flex items-center justify-between text-xs">
            <span className={requirement.trim().length < 10 && requirement.length > 0 ? 'text-red-400' : 'text-slate-400'}>
              {requirement.trim().length < 10 ? `Mínimo 10 caracteres (${requirement.trim().length}/10)` : `${requirement.length} caracteres`}
            </span>
          </div>
        </div>

        {/* Agent selector */}
        <div className="space-y-2">
          <label className="block text-sm font-semibold text-slate-700">Agente a ejecutar</label>
          <select
            value={agent}
            onChange={e => setAgent(e.target.value)}
            className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-white transition cursor-pointer"
          >
            {AGENTS.map(a => (
              <option key={a.value} value={a.value}>
                {a.icon}  {a.label}
              </option>
            ))}
          </select>

          {/* Selected agent description */}
          {selected && (
            <div className="flex items-start gap-2.5 mt-2">
              <span className={`shrink-0 px-2.5 py-0.5 rounded-full text-xs font-semibold ${selected.badgeColor}`}>
                {selected.badge}
              </span>
              <p className="text-xs text-slate-500 leading-relaxed">{selected.desc}</p>
            </div>
          )}

          {/* HITL warning */}
          {agent === '4' && (
            <div className="flex items-start gap-2.5 bg-purple-50 border border-purple-200 rounded-xl px-4 py-3 text-xs text-purple-700 mt-2">
              <span className="text-base shrink-0 leading-none mt-0.5">🧑‍💻</span>
              <span>
                El Agente 4 detectará ambigüedades en tu requerimiento y te pedirá que las resuelvas manualmente antes de generar el resultado final.
              </span>
            </div>
          )}

          {/* Pipeline M1+M2 info */}
          {agent === '5' && (
            <div className="flex items-start gap-2.5 bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3 text-xs text-emerald-700 mt-2">
              <span className="text-base shrink-0 leading-none mt-0.5">🔬</span>
              <span>
                El Agente 5 ejecuta el pipeline completo en tiempo real vía WebSocket: resolverás ambigüedades (M1), revisarás cada escenario Gherkin y aprobarás el suite (M2). Al finalizar se genera el Acta de Aprobación HTML.
              </span>
            </div>
          )}
        </div>

        {/* top_k slider */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-sm font-semibold text-slate-700">
              Historias de referencia
            </label>
            <span className="text-sm font-bold text-indigo-600 bg-indigo-50 px-2.5 py-0.5 rounded-lg">
              top_k = {topK}
            </span>
          </div>
          <input
            type="range"
            min={1}
            max={10}
            value={topK}
            onChange={e => setTopK(Number(e.target.value))}
            className="w-full accent-indigo-600 cursor-pointer"
          />
          <p className="text-xs text-slate-400">
            Cuántas historias similares del knowledge base se usarán como referencia para el LLM.
          </p>
        </div>

        {/* Submit button */}
        <button
          onClick={onSubmit}
          disabled={!isValid}
          className="w-full py-3.5 rounded-xl bg-indigo-600 text-white font-semibold text-sm hover:bg-indigo-700 active:bg-indigo-800 disabled:opacity-40 disabled:cursor-not-allowed transition shadow-sm flex items-center justify-center gap-2"
        >
          <span>Analizar con Agente {agent}</span>
          <span className="text-base">{selected?.icon}</span>
        </button>
      </div>
    </div>
  )
}
