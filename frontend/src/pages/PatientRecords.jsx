import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { getQueue } from '../api'
import PriorityBadge from '../components/PriorityBadge'

const URGENCY_FILTERS = ['all', 'critical', 'high', 'moderate', 'low']

export default function PatientRecords() {
  const [queue, setQueue] = useState(null)
  const [filter, setFilter] = useState('all')
  const [search, setSearch] = useState('')
  const navigate = useNavigate()

  useEffect(() => { getQueue().then(setQueue) }, [])

  const rows = (queue || []).filter(p => {
    if (filter !== 'all' && p.urgency !== filter) return false
    if (search && !`${p.name} ${p.external_id}`.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 18, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1>Patient Records</h1>
          <p className="subtitle" style={{ marginBottom: 0 }}>Full triage queue — every patient assessed by the pipeline, most urgent first.</p>
        </div>
        <Link to="/new" className="btn btn-primary">＋ New Patient</Link>
      </div>

      <div className="card">
        <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
          <input
            placeholder="Search by name or ID…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ padding: '9px 12px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--surface-2)', color: 'var(--text-primary)', minWidth: 220 }}
          />
          <div style={{ display: 'flex', gap: 6 }}>
            {URGENCY_FILTERS.map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className="btn"
                style={{
                  padding: '6px 12px', fontSize: 12.5, textTransform: 'capitalize',
                  background: filter === f ? 'var(--brand-navy)' : 'var(--surface-2)',
                  color: filter === f ? 'white' : 'var(--text-primary)',
                  borderColor: filter === f ? 'var(--brand-navy)' : 'var(--border)',
                }}
              >
                {f}
              </button>
            ))}
          </div>
          <span className="field-hint" style={{ marginLeft: 'auto' }}>{rows.length} of {queue?.length ?? 0} patients</span>
        </div>

        {!queue ? (
          <div className="empty-state">Loading…</div>
        ) : rows.length === 0 ? (
          <div className="empty-state">No matching patients.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Patient</th><th>Age</th><th>Urgency</th><th>Risk</th><th>Predicted</th><th>Last stage reached</th><th>Recommendation</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(p => (
                <tr key={p.id} onClick={() => navigate(`/patients/${p.id}`)}>
                  <td><strong>{p.name}</strong><div className="field-hint">{p.external_id}</div></td>
                  <td>{p.age}</td>
                  <td><PriorityBadge urgency={p.urgency} /></td>
                  <td>{p.final_risk_probability != null ? `${(p.final_risk_probability * 100).toFixed(0)}%` : '—'}</td>
                  <td>{p.predicted_class || '—'}</td>
                  <td style={{ textTransform: 'capitalize' }}>{p.last_stage || '—'}</td>
                  <td className="field-hint">{p.recommendation || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
