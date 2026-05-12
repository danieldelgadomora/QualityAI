import { useCallback, useEffect, useReducer, useRef } from 'react'
import { WS_PIPELINE_URL } from '../services/api'

const INITIAL_STATE = {
  connectionStatus: 'idle',       // idle | connecting | connected | closed | error
  pipelineState: 'idle',          // idle | m1_running | m1_waiting_resolutions |
                                  // m2_generating | m2_waiting_reviewer_id | m2_reviewing |
                                  // m2_waiting_global | saving | completed | error
  statusMessage: '',
  ambiguities: [],
  contractA: null,
  m2Progress: { done: 0, total: 0 },
  totalScenarios: 0,
  currentScenario: null,          // { scenario, index, total }
  coverageComparison: null,       // { reclassifications, before, after }
  pipelineResult: null,           // { status, contract_b_run_id, total_scenarios, acta_html }
  error: null,
}

function reducer(state, action) {
  switch (action.type) {
    case 'WS_CONNECTING':
      return { ...state, connectionStatus: 'connecting' }
    case 'WS_OPEN':
      return { ...state, connectionStatus: 'connected' }
    case 'WS_CLOSED':
      return { ...state, connectionStatus: 'closed' }
    case 'WS_ERROR':
      return { ...state, connectionStatus: 'error', error: action.message }
    case 'RESET':
      return INITIAL_STATE

    case 'status_update':
      return { ...state, statusMessage: action.message, pipelineState: state.pipelineState === 'idle' ? 'm1_running' : state.pipelineState }

    case 'm1_ambiguities_detected':
      return { ...state, pipelineState: 'm1_waiting_resolutions', ambiguities: action.ambiguities }

    case 'm1_completed':
      return {
        ...state,
        pipelineState: 'm2_generating',
        contractA: action.contract_a,
        ambiguities: [],
        statusMessage: 'Contract A generado. Generando escenarios Gherkin...',
      }

    case 'm2_progress':
      return {
        ...state,
        m2Progress: { done: action.done_acs, total: action.total_acs },
        statusMessage: `Generando ${action.ac_id}... (${action.done_acs}/${action.total_acs} AC)`,
      }

    case 'm2_completed':
      return { ...state, totalScenarios: action.total_scenarios, statusMessage: 'Generación completada.' }

    case 'scenario_review_prompt':
      if (action.scenario_index === -1)
        return { ...state, pipelineState: 'm2_waiting_reviewer_id' }
      return {
        ...state,
        pipelineState: 'm2_reviewing',
        currentScenario: {
          scenario: action.scenario,
          index: action.scenario_index,
          total: action.total_scenarios,
        },
      }

    case 'global_decision_prompt':
      return {
        ...state,
        pipelineState: 'm2_waiting_global',
        coverageComparison: {
          reclassifications: action.reclassifications,
          before: action.coverage_before,
          after: action.coverage_after,
        },
      }

    case 'pipeline_completed':
      return { ...state, pipelineState: 'completed', pipelineResult: action }

    case 'pipeline_error':
      return { ...state, pipelineState: 'error', error: action.message }

    default:
      return state
  }
}

export function usePipelineWebSocket() {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE)
  const wsRef = useRef(null)

  function _connect() {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    dispatch({ type: 'WS_CONNECTING' })
    const ws = new WebSocket(WS_PIPELINE_URL)
    wsRef.current = ws

    ws.onopen = () => dispatch({ type: 'WS_OPEN' })

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data)
        dispatch(msg)
      } catch {
        dispatch({ type: 'pipeline_error', message: 'Mensaje del servidor malformado' })
      }
    }

    ws.onclose = () => dispatch({ type: 'WS_CLOSED' })
    ws.onerror = () => dispatch({ type: 'WS_ERROR', message: 'Error de conexión WebSocket' })
  }

  const _send = useCallback((msg) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg))
    }
  }, [])

  const startPipeline = useCallback((requirementText, topK, interactiveM1) => {
    _connect()
    // Pequeña espera para garantizar que el WS esté abierto antes de enviar
    const timer = setTimeout(() => {
      _send({ type: 'start_pipeline', requirement_text: requirementText, top_k: topK, interactive_m1: interactiveM1 })
    }, 150)
    return () => clearTimeout(timer)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [_send])

  const resolveAmbiguities = useCallback((resolutions) =>
    _send({ type: 'resolve_ambiguities', resolutions }), [_send])

  const sendReviewerId = useCallback((reviewer) =>
    _send({ type: 'reviewer_id', reviewer }), [_send])

  const submitScenarioAction = useCallback((scenarioIndex, action, opts = {}) =>
    _send({ type: 'scenario_action', scenario_index: scenarioIndex, action, ...opts }), [_send])

  const submitGlobalDecision = useCallback((decision, feedback = '') =>
    _send({ type: 'global_decision', decision, feedback: feedback || null }), [_send])

  const reset = useCallback(() => {
    wsRef.current?.close()
    wsRef.current = null
    dispatch({ type: 'RESET' })
  }, [])

  useEffect(() => {
    return () => {
      wsRef.current?.close()
    }
  }, [])

  return {
    state,
    startPipeline,
    resolveAmbiguities,
    sendReviewerId,
    submitScenarioAction,
    submitGlobalDecision,
    reset,
  }
}
