import { useState } from 'react'
import RequirementForm from './components/RequirementForm'
import PipelineView from './components/PipelineView'

export default function App() {
  const [phase, setPhase] = useState('form') // form | pipeline
  const [requirement, setRequirement] = useState('')
  const [topK, setTopK] = useState(3)

  function handleAnalyze() {
    if (requirement.trim().length < 10) return
    setPhase('pipeline')
  }

  function reset() {
    setPhase('form')
  }

  return (
    <div className="min-h-screen bg-slate-50 font-sans">
      <header className="bg-indigo-700 text-white shadow-md sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center gap-3">
          <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center text-lg font-bold">Q</div>
          <div>
            <h1 className="text-lg font-bold tracking-tight leading-none">QualityAI</h1>
            <p className="text-indigo-300 text-xs mt-0.5">Pipeline M1+M2 — Refinamiento y Generación de Pruebas</p>
          </div>
          {phase !== 'form' && (
            <button
              onClick={reset}
              className="ml-auto text-xs text-indigo-200 hover:text-white transition px-3 py-1.5 rounded-lg hover:bg-white/10"
            >
              ← Nueva consulta
            </button>
          )}
        </div>
      </header>

      {phase === 'pipeline' && (
        <div className="bg-white border-b border-slate-100">
          <div className="max-w-4xl mx-auto px-6 py-2 flex items-center gap-2 text-xs text-slate-400">
            <span className="text-slate-600 font-medium">Pipeline M1+M2</span>
            <span>›</span>
            <span className="text-emerald-600 font-medium">En ejecución</span>
          </div>
        </div>
      )}

      <main className="max-w-4xl mx-auto px-6 py-10">
        {phase === 'form' && (
          <RequirementForm
            requirement={requirement}
            setRequirement={setRequirement}
            topK={topK}
            setTopK={setTopK}
            onSubmit={handleAnalyze}
          />
        )}

        {phase === 'pipeline' && (
          <PipelineView
            requirement={requirement}
            topK={topK}
            interactiveM1={true}
            onBack={reset}
          />
        )}
      </main>
    </div>
  )
}
