import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getAssistantStatus, getPatient, API_BASE_URL } from '../api'

const SUGGESTIONS = [
  "What's the difference between MCI and Alzheimer's disease?",
  'What does a CSF phosphorylated tau result actually mean?',
  'How should I talk to a parent who just got a high-risk result?',
  'What lifestyle changes actually help slow cognitive decline?',
]

async function streamChat(messages, patientContext, onToken, onDone, onError) {
  const token = localStorage.getItem('bt_token')
  const resp = await fetch(`${API_BASE_URL}/api/assistant/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ messages, patient_context: patientContext }),
  })
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}))
    onError(body.detail || `Request failed (${resp.status})`)
    return
  }
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n\n')
    buffer = lines.pop()
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const payload = line.slice(6)
      if (payload === '[DONE]') { onDone(); return }
      try {
        const parsed = JSON.parse(payload)
        if (parsed.error) { onError(parsed.error); return }
        if (parsed.text) onToken(parsed.text)
      } catch { /* ignore partial parse */ }
    }
  }
  onDone()
}

export default function AIAssistant() {
  const [searchParams] = useSearchParams()
  const patientId = searchParams.get('patientId')
  const [status, setStatus] = useState(null)
  const [patient, setPatient] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [error, setError] = useState(null)
  const bottomRef = useRef(null)

  useEffect(() => { getAssistantStatus().then(setStatus) }, [])
  useEffect(() => { if (patientId) getPatient(patientId).then(setPatient) }, [patientId])
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const patientContext = patient?.last_result ? {
    name: patient.name,
    age: patient.age,
    predicted_class: patient.last_result.predicted_class,
    final_risk_probability: patient.last_result.final_risk_probability,
    urgency: patient.last_result.urgency,
    last_stage: patient.last_result.last_stage,
    recommendation: patient.last_result.recommendation,
    top_contributors: patient.last_result.stage_results?.at(-1)?.top_contributors,
  } : null

  const send = async (text) => {
    if (!text.trim() || streaming) return
    setError(null)
    const nextMessages = [...messages, { role: 'user', content: text }]
    setMessages([...nextMessages, { role: 'assistant', content: '' }])
    setInput('')
    setStreaming(true)

    await streamChat(
      nextMessages, patientContext,
      (token) => setMessages(prev => {
        const copy = [...prev]
        copy[copy.length - 1] = { role: 'assistant', content: copy[copy.length - 1].content + token }
        return copy
      }),
      () => setStreaming(false),
      (err) => { setError(err); setStreaming(false); setMessages(prev => prev.slice(0, -1)) },
    )
  }

  return (
    <div>
      <h1>AI Assistant</h1>
      <p className="subtitle">
        Ask about Alzheimer's, dementia care, or (when opened from a patient) this
        patient's specific result. Not a diagnostic tool — always confirm with a clinician.
      </p>

      {patient && (
        <div className="disclaimer" style={{ marginBottom: 16 }}>
          Grounded in <strong>{patient.name}</strong>'s current triage result ({patient.last_result?.predicted_class}, {(patient.last_result?.final_risk_probability * 100).toFixed(0)}% risk).
        </div>
      )}

      {status?.configured === false && (
        <div className="card">
          <h3>AI Assistant not configured</h3>
          <p style={{ fontSize: 14, lineHeight: 1.6 }}>
            This feature calls the Claude API server-side. To enable it:
          </p>
          <ol style={{ fontSize: 14, lineHeight: 1.8, paddingLeft: 20 }}>
            <li>Copy <code>backend/.env.example</code> to <code>backend/.env</code></li>
            <li>Set <code>ANTHROPIC_API_KEY=your-key</code></li>
            <li>Restart the backend (<code>uvicorn app.main:app --reload --port 8000</code>)</li>
          </ol>
        </div>
      )}

      {status?.configured && (
        <div className="card" style={{ display: 'flex', flexDirection: 'column', height: 520 }}>
          <div style={{ flex: 1, overflowY: 'auto', paddingRight: 4 }}>
            {messages.length === 0 && (
              <div>
                <div className="field-hint" style={{ marginBottom: 10 }}>Try asking:</div>
                {SUGGESTIONS.map(s => (
                  <div key={s} onClick={() => send(s)}
                       style={{ padding: '10px 12px', borderRadius: 10, border: '1px solid var(--border)', marginBottom: 8, cursor: 'pointer', fontSize: 13.5 }}>
                    {s}
                  </div>
                ))}
              </div>
            )}
            {messages.map((m, i) => (
              <div key={i} style={{
                marginBottom: 14, maxWidth: '85%',
                marginLeft: m.role === 'user' ? 'auto' : 0,
                background: m.role === 'user' ? 'var(--series-1)' : 'var(--surface-2)',
                color: m.role === 'user' ? 'white' : 'var(--text-primary)',
                padding: '10px 14px', borderRadius: 14,
                fontSize: 14, lineHeight: 1.6, whiteSpace: 'pre-wrap',
              }}>
                {m.content || (streaming && i === messages.length - 1 ? '…' : '')}
              </div>
            ))}
            <div ref={bottomRef} />
          </div>

          {error && <div className="error-banner">{error}</div>}

          <form onSubmit={e => { e.preventDefault(); send(input) }} style={{ display: 'flex', gap: 8, marginTop: 10 }}>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask a question…"
              disabled={streaming}
              style={{ flex: 1, padding: '10px 12px', borderRadius: 10, border: '1px solid var(--border)', background: 'var(--surface-2)', color: 'var(--text-primary)' }}
            />
            <button className="btn btn-primary" type="submit" disabled={streaming || !input.trim()}>
              {streaming ? 'Thinking…' : 'Send'}
            </button>
          </form>
        </div>
      )}
    </div>
  )
}
