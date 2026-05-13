export default function RequirementForm({ requirement, setRequirement, topK, setTopK, onSubmit }) {
  const isValid = requirement.trim().length >= 10

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold text-slate-800 tracking-tight">Pipeline M1+M2</h2>
        <p className="text-slate-500 text-sm mt-2">
          Describe el requerimiento en lenguaje natural. El pipeline refinará ambigüedades (M1),
          generará escenarios Gherkin con ISO 25010 (M2) y producirá el Acta de Aprobación.
        </p>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-8 space-y-7">

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
              {requirement.trim().length < 10
                ? `Mínimo 10 caracteres (${requirement.trim().length}/10)`
                : `${requirement.length} caracteres`}
            </span>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-sm font-semibold text-slate-700">Historias de referencia</label>
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

        <div className="flex items-start gap-2.5 bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3 text-xs text-emerald-700">
          <span className="text-base shrink-0 leading-none mt-0.5">🔬</span>
          <span>
            El pipeline ejecuta M1 (detección y resolución interactiva de ambigüedades) seguido de M2
            (generación de escenarios Gherkin clasificados con ISO 25010, revisión escenario a escenario
            y decisión global). Al aprobar el suite se genera el Acta de Aprobación HTML.
          </span>
        </div>

        <button
          onClick={onSubmit}
          disabled={!isValid}
          className="w-full py-3.5 rounded-xl bg-indigo-600 text-white font-semibold text-sm hover:bg-indigo-700 active:bg-indigo-800 disabled:opacity-40 disabled:cursor-not-allowed transition shadow-sm flex items-center justify-center gap-2"
        >
          <span>Iniciar Pipeline M1+M2</span>
          <span className="text-base">🔬</span>
        </button>
      </div>
    </div>
  )
}
