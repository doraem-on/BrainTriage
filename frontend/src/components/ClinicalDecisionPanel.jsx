import { useEffect, useState } from 'react'
import { recordDecision, getDecisions } from '../api'

const OVERRIDE_REASONS = [
  'Clinical exam inconsistent with AI result',
  'Additional history changes risk assessment',
  'Patient/family declines further testing',
  'Data quality concern (measurement, input error)',
  'Other',
]

export default function ClinicalDecisionPanel({ patientId }) {
  const [decisions, setDecisions] = useState(null)
  const [showOverride, setShowOverride] = useState(false)
  const [reason, setReason] = useState(OVERRIDE_REASONS[0])
  const [note, setNote] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const load = () => getDecisions(patientId).then(setDecisions)
  useEffect(load, [patientId]) // eslint-disable-line react-hooks/exhaustive-deps

  const submit = async (decision) => {
    setSubmitting(true)
    setError(null)
    try {
      await recordDecision(patientId, {
        decision,
        override_reason: decision === 'override' ? reason : null,
        override_note: decision === 'override' ? (note || null) : null,
      })
      setShowOverride(false)
      setNote('')
      load()
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to record decision.')
    } finally {
      setSubmitting(false)
    }
  }

  const latest = decisions?.[0]

  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <h3>Clinical Decision</h3>
      <div className="disclaimer" style={{ marginBottom: 14 }}>
        Decision-support only — not an autonomous diagnosis. Every recommendation requires clinician review before acting on it.
      </div>

      {latest && (
        <div className="field-hint" style={{ marginBottom: 12 }}>
          Latest: <strong style={{ color: latest.decision === 'override' ? 'var(--status-warning)' : 'var(--status-good)' }}>
            {latest.decision === 'override' ? 'Overridden' : 'Accepted'}
          </strong> by {latest.decided_by} on {new Date(latest.decided_at).toLocaleString()}
          {latest.override_reason && <> — {latest.override_reason}</>}
        </div>
      )}

      {error && <div className="error-banner">{error}</div>}

      {!showOverride ? (
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-primary" onClick={() => submit('accept')} disabled={submitting}>
            ✓ Accept AI recommendation
          </button>
          <button className="btn" onClick={() => setShowOverride(true)} disabled={submitting}>
            ✕ Override
          </button>
        </div>
      ) : (
        <div>
          <div className="field" style={{ marginBottom: 10 }}>
            <label>Reason for override</label>
            <select value={reason} onChange={e => setReason(e.target.value)}>
              {OVERRIDE_REASONS.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div className="field" style={{ marginBottom: 12 }}>
            <label>Additional note (optional)</label>
            <input value={note} onChange={e => setNote(e.target.value)} placeholder="Clinical context…" />
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-primary" onClick={() => submit('override')} disabled={submitting}>
              {submitting ? 'Recording…' : 'Confirm Override'}
            </button>
            <button className="btn" onClick={() => setShowOverride(false)}>Cancel</button>
          </div>
        </div>
      )}

      {decisions?.length > 0 && (
        <details style={{ marginTop: 16 }}>
          <summary className="field-hint" style={{ cursor: 'pointer', fontWeight: 700 }}>Audit trail ({decisions.length})</summary>
          <table style={{ marginTop: 10 }}>
            <thead><tr><th>When</th><th>By</th><th>Decision</th><th>Reason</th></tr></thead>
            <tbody>
              {decisions.map(d => (
                <tr key={d.id} style={{ cursor: 'default' }}>
                  <td className="field-hint">{new Date(d.decided_at).toLocaleString()}</td>
                  <td>{d.decided_by}</td>
                  <td style={{ textTransform: 'capitalize' }}>{d.decision}</td>
                  <td className="field-hint">{d.override_reason || '—'}{d.override_note ? ` (${d.override_note})` : ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      )}
    </div>
  )
}
