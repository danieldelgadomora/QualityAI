import { useState } from 'react'
import RequirementForm from './components/RequirementForm'
import HITLReview from './components/HITLReview'
import ResultView from './components/ResultView'
import { analyzeWithAgent, hitlStart, hitlResolve } from './services/api'

const LOADING_MESSAGES = {
  agent: 'El agente está procesando tu requerimiento...',
  hitl_start: 'Detectando ambigüedades...',
  hitl_resolve: 'Generando requerimiento refinado con tus resoluciones...',
}

export default function App() {
  const [phase, setPhase] = useState('form') // form | loading | hitl | result | error
  const [loadingMsg, setLoadingMsg] = useState('')
  const [agent, setAgent] = useState('3')
  const [requirement, setRequirement] = useState('')
  const [topK, setTopK] = useState(3)
  const [hitlData, setHitlData] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  async function handleAnalyze() {
    if (requirement.trim().length < 10) return
    setError('')

    try {
      if (agent === '4') {
        setLoadingMsg(LOADING_MESSAGES.hitl_start)
        setPhase('loading')
        const startData = await hitlStart(requirement, topK)

        if (startData.requires_review) {
          setHitlData(startData)
          setPhase('hitl')
        } else {
          // Sin ambigüedades: resolver directamente con lista vacía
          setLoadingMsg(LOADING_MESSAGES.hitl_resolve)
          const jobData = await hitlResolve(startData.session_id, [])
          setResult({ agent, data: jobData })
          setPhase('result')
        }
      } else {
        setLoadingMsg(LOADING_MESSAGES.agent)
        setPhase('loading')
        const data = await analyzeWithAgent(agent, requirement, topK)
        setResult({ agent, data })
        setPhase('result')
      }
    } catch (err) {
      setError(err.message || 'Error inesperado')
      setPhase('error')
    }
  }

  async function handleHITLSubmit(resolutions) {
    setLoadingMsg(LOADING_MESSAGES.hitl_resolve)
    setPhase('loading')
    try {
      const data = await hitlResolve(hitlData.session_id, resolutions)
      setResult({ agent: '4', data })
      setPhase('result')
    } catch (err) {
      setError(err.message || 'Error al procesar las resoluciones')
      setPhase('error')
    }
  }

  function reset() {
    setPhase('form')
    setResult(null)
    setHitlData(null)
    setError('')
    setLoadingMsg('')
  }

  return (
    <div className="min-h-screen bg-slate-50 font-sans">
      {/* Header */}
      <header className="bg-indigo-700 text-white shadow-md sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center gap-3">
          <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center text-lg font-bold">Q</div>
          <div>
            <h1 className="text-lg font-bold tracking-tight leading-none">QualityAI</h1>
            <p className="text-indigo-300 text-xs mt-0.5">Refinamiento inteligente de requerimientos</p>
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

      {/* Breadcrumb / step indicator */}
      {phase !== 'form' && (
        <div className="bg-white border-b border-slate-100">
          <div className="max-w-4xl mx-auto px-6 py-2 flex items-center gap-2 text-xs text-slate-400">
            <span className="text-slate-600 font-medium">Agente {agent}</span>
            <span>›</span>
            {phase === 'loading' && <span className="text-indigo-500">{loadingMsg}</span>}
            {phase === 'hitl' && <span className="text-amber-600 font-medium">Revisión de ambigüedades</span>}
            {phase === 'result' && <span className="text-green-600 font-medium">Resultado generado</span>}
            {phase === 'error' && <span className="text-red-500">Error</span>}
          </div>
        </div>
      )}

      <main className="max-w-4xl mx-auto px-6 py-10">
        {phase === 'form' && (
          <RequirementForm
            requirement={requirement}
            setRequirement={setRequirement}
            agent={agent}
            setAgent={setAgent}
            topK={topK}
            setTopK={setTopK}
            onSubmit={handleAnalyze}
          />
        )}

        {phase === 'loading' && (
          <div className="flex flex-col items-center justify-center py-32 gap-5">
            <div className="relative w-16 h-16">
              <div className="absolute inset-0 rounded-full border-4 border-indigo-100" />
              <div className="absolute inset-0 rounded-full border-4 border-indigo-600 border-t-transparent animate-spin" />
            </div>
            <div className="text-center">
              <p className="text-slate-700 font-medium">{loadingMsg}</p>
              <p className="text-slate-400 text-sm mt-1">Esto puede tardar unos segundos</p>
            </div>
          </div>
        )}

        {phase === 'hitl' && hitlData && (
          <HITLReview
            hitlData={hitlData}
            onSubmit={handleHITLSubmit}
            onCancel={reset}
          />
        )}

        {phase === 'result' && result && (
          <ResultView result={result} onBack={reset} />
        )}

        {phase === 'error' && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-10 text-center space-y-4">
            <div className="text-4xl">⚠️</div>
            <div>
              <p className="text-red-700 font-semibold text-lg">Ocurrió un error</p>
              <p className="text-red-500 text-sm mt-1 max-w-md mx-auto">{error}</p>
            </div>
            <button
              onClick={reset}
              className="px-6 py-2.5 bg-red-600 text-white rounded-xl hover:bg-red-700 text-sm font-medium transition shadow-sm"
            >
              Volver al inicio
            </button>
          </div>
        )}
      </main>
    </div>
  )
}
