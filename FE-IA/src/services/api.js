const BASE = '/api/v1'

async function request(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await res.json()
  if (!res.ok) {
    const detail = Array.isArray(data.detail)
      ? data.detail.map(e => e.msg).join(', ')
      : data.detail ?? `Error ${res.status}`
    throw new Error(detail)
  }
  return data
}

export const analyzeWithAgent = (agent, requirement_text, top_k) =>
  request(`${BASE}/requirements/agente${agent}`, { requirement_text, top_k })

export const hitlStart = (requirement_text, top_k) =>
  request(`${BASE}/hitl/start`, { requirement_text, top_k })

export const hitlResolve = (session_id, resolutions) =>
  request(`${BASE}/hitl/resolve`, { session_id, resolutions })
