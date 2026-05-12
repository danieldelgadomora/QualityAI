import { useState } from 'react'

const PRIORITY = {
  critical: { label: 'Crítica', cls: 'bg-red-100 text-red-700' },
  high:     { label: 'Alta',    cls: 'bg-orange-100 text-orange-700' },
  medium:   { label: 'Media',   cls: 'bg-blue-100 text-blue-700' },
  low:      { label: 'Baja',    cls: 'bg-slate-100 text-slate-500' },
}

const STORY_TYPE = {
  functional:     { label: 'Funcional',    cls: 'bg-indigo-100 text-indigo-700' },
  non_functional: { label: 'No funcional', cls: 'bg-purple-100 text-purple-700' },
  technical:      { label: 'Técnica',      cls: 'bg-teal-100 text-teal-700' },
}

function AcceptanceCriterion({ ac }) {
  return (
    <div className={`rounded-xl border p-3.5 text-xs space-y-2 ${ac.is_negative_case ? 'bg-red-50 border-red-100' : 'bg-white border-slate-100'}`}>
      <div className="flex items-center gap-2 flex-wrap">
        <span className="font-mono font-bold text-slate-400">{ac.id}</span>
        {ac.is_negative_case && (
          <span className="bg-red-100 text-red-600 px-1.5 py-0.5 rounded-md text-xs font-medium">Negativo</span>
        )}
        <span className="text-slate-700 font-medium">{ac.description}</span>
      </div>
      <div className="space-y-1 text-slate-600 pl-1 border-l-2 border-slate-200 ml-1">
        <p><span className="font-bold text-slate-400 mr-1.5">GIVEN</span>{ac.given}</p>
        <p><span className="font-bold text-slate-400 mr-1.5">WHEN</span>{ac.when}</p>
        <p><span className="font-bold text-slate-400 mr-1.5">THEN</span>{ac.then}</p>
      </div>
      {ac.boundary_values?.length > 0 && (
        <p className="text-slate-400 text-xs pt-1">
          Valores límite: {ac.boundary_values.join(' · ')}
        </p>
      )}
      {ac.test_data_examples?.length > 0 && (
        <div className="text-slate-400 text-xs pt-1">
          <span className="font-medium">Datos de prueba:</span>{' '}
          {ac.test_data_examples.map((ex, i) => (
            <span key={i} className="font-mono bg-slate-100 px-1.5 py-0.5 rounded mr-1">
              {JSON.stringify(ex)}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function UserStoryCard({ story, index }) {
  const [open, setOpen] = useState(index === 0) // first story open by default
  const priority = PRIORITY[story.priority] ?? PRIORITY.medium
  const type = STORY_TYPE[story.story_type] ?? STORY_TYPE.functional
  const negativeCount = story.acceptance_criteria.filter(ac => ac.is_negative_case).length

  return (
    <div className="bg-white border border-slate-100 rounded-2xl overflow-hidden shadow-sm">
      {/* Header (clickable) */}
      <button
        className="w-full text-left px-5 py-4 flex items-start justify-between gap-4 hover:bg-slate-50 transition"
        onClick={() => setOpen(o => !o)}
      >
        <div className="space-y-1.5 flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-xs font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-lg">
              {story.id}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${priority.cls}`}>
              {priority.label}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${type.cls}`}>
              {type.label}
            </span>
          </div>
          <p className="font-semibold text-slate-800 text-sm leading-snug">{story.title}</p>
          <p className="text-xs text-slate-500 leading-relaxed">
            Como <em className="not-italic font-medium text-slate-600">{story.as_a}</em>,
            {' '}quiero <em className="not-italic font-medium text-slate-600">{story.i_want}</em>,
            {' '}para que <em className="not-italic font-medium text-slate-600">{story.so_that}</em>
          </p>
        </div>
        <div className="shrink-0 flex items-center gap-2 text-xs text-slate-400 pt-0.5">
          <span>{story.acceptance_criteria.length} criterios</span>
          {negativeCount > 0 && (
            <span className="text-red-400">{negativeCount} neg.</span>
          )}
          <span className="text-slate-300">{open ? '▲' : '▼'}</span>
        </div>
      </button>

      {/* Expanded content */}
      {open && (
        <div className="border-t border-slate-100 bg-slate-50/50 px-5 py-5 space-y-5">
          {/* Acceptance criteria */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Criterios de aceptación ({story.acceptance_criteria.length})
            </h4>
            <div className="space-y-2">
              {story.acceptance_criteria.map(ac => (
                <AcceptanceCriterion key={ac.id} ac={ac} />
              ))}
            </div>
          </div>

          {/* Business rules */}
          {story.business_rules?.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Reglas de negocio</h4>
              <ul className="space-y-1">
                {story.business_rules.map((rule, i) => (
                  <li key={i} className="text-xs text-slate-600 flex items-start gap-2">
                    <span className="text-slate-300 shrink-0">•</span>{rule}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Ambiguities resolved */}
          {story.ambiguities_resolved?.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Ambigüedades resueltas ({story.ambiguities_resolved.length})
              </h4>
              <div className="space-y-1.5">
                {story.ambiguities_resolved.map((amb, i) => (
                  <div key={i} className="text-xs text-slate-600 flex items-start gap-2">
                    <span className="shrink-0 mt-0.5">
                      {amb.assumption_made ? '⚠️' : '✅'}
                    </span>
                    <span>
                      <em className="not-italic font-medium text-slate-700">"{amb.original_text}"</em>
                      {' → '}
                      {amb.resolution}
                      {amb.assumption_made && (
                        <span className="text-amber-500 ml-1">[suposición del LLM]</span>
                      )}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/* ────────────────────────────────────────────────────────── */

export default function ResultView({ result, onBack }) {
  const { agent, data } = result

  /* Agent 1 — plain text */
  if (agent === '1') {
    return (
      <div className="space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-slate-800 tracking-tight">Resultado — Agente 1</h2>
            <p className="text-slate-500 text-sm mt-1">Salida en texto libre (RAG básico, sin estructura JSON)</p>
          </div>
          <button onClick={onBack} className="shrink-0 px-4 py-2 text-sm rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 transition">
            ← Nueva consulta
          </button>
        </div>
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6">
          <pre className="whitespace-pre-wrap text-sm text-slate-700 leading-relaxed font-sans">{data.result_text}</pre>
        </div>
      </div>
    )
  }

  /* Agents 2, 3, 4 — structured JobResponse */
  const job = data
  const refined = job?.result

  const agentLabels = { '2': 'Agente 2', '3': 'Agente 3', '4': 'Agente 4 — HITL' }

  if (job?.status === 'failed') {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-slate-800">Error en el agente</h2>
          <button onClick={onBack} className="px-4 py-2 text-sm rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 transition">
            ← Nueva consulta
          </button>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-2xl p-6">
          <p className="text-red-600 text-sm leading-relaxed">{job.error}</p>
        </div>
      </div>
    )
  }

  const stories = refined?.user_stories ?? []
  const totalCriteria = stories.reduce((acc, s) => acc + s.acceptance_criteria.length, 0)
  const zeroAssumptions = agent === '4' && refined?.total_assumptions_made === 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 tracking-tight">
            Resultado — {agentLabels[agent]}
          </h2>
          <p className="text-slate-400 text-xs mt-1">
            {job.run_id} · v{refined?.agent_version}
          </p>
        </div>
        <button
          onClick={onBack}
          className="shrink-0 px-4 py-2 text-sm rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 transition"
        >
          ← Nueva consulta
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: 'Historias', value: stories.length, color: 'text-indigo-600', icon: '📋' },
          { label: 'Criterios', value: totalCriteria, color: 'text-blue-600', icon: '✅' },
          { label: 'Ambigüedades', value: refined?.total_ambiguities_found ?? 0, color: 'text-amber-600', icon: '🔍' },
          {
            label: 'Suposiciones',
            value: refined?.total_assumptions_made ?? 0,
            color: (refined?.total_assumptions_made ?? 0) === 0 ? 'text-emerald-600' : 'text-red-500',
            icon: (refined?.total_assumptions_made ?? 0) === 0 ? '🎯' : '⚠️',
          },
        ].map(s => (
          <div key={s.label} className="bg-white rounded-xl border border-slate-100 shadow-sm p-4 text-center">
            <p className="text-xl mb-0.5">{s.icon}</p>
            <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-xs text-slate-400 mt-0.5">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Zero assumptions badge (agent 4 only) */}
      {zeroAssumptions && (
        <div className="flex items-center gap-3 bg-emerald-50 border border-emerald-200 rounded-xl px-5 py-3.5 text-sm text-emerald-700">
          <span className="text-xl">🎯</span>
          <span>
            <strong>Cero suposiciones.</strong> Todas las ambigüedades fueron resueltas por el analista — el resultado no contiene inferencias del LLM.
          </span>
        </div>
      )}

      {/* Project context */}
      {refined?.project_context && (
        <div className="bg-white border border-slate-100 rounded-xl shadow-sm px-5 py-4">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Contexto del proyecto</p>
          <p className="text-sm text-slate-700 leading-relaxed">{refined.project_context}</p>
        </div>
      )}

      {/* Coverage notes */}
      {refined?.coverage_notes && (
        <div className="bg-amber-50 border border-amber-100 rounded-xl px-5 py-4 text-sm text-amber-700">
          <span className="font-semibold">Notas de cobertura: </span>{refined.coverage_notes}
        </div>
      )}

      {/* User stories */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Historias de usuario ({stories.length})
        </h3>
        {stories.map((story, i) => (
          <UserStoryCard key={story.id} story={story} index={i} />
        ))}
      </div>
    </div>
  )
}
