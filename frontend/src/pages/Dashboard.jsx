import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getQueue, getQueueStats } from '../api'
import PriorityBadge from '../components/PriorityBadge'
import StatTile from '../components/StatTile'
import ModelCard from '../components/ModelCard'

export default function Dashboard() {
  const [queue, setQueue] = useState(null)
  const [stats, setStats] = useState(null)
  const navigate = useNavigate()

  const load = () => {
    getQueue().then(setQueue)
    getQueueStats().then(setStats)
  }

  useEffect(load, [])

  return (
    <div>
      <h1>Triage Dashboard</h1>
      <p className="subtitle">Patients ranked by AI-prioritized urgency across the adaptive Cognitive → Blood → MRI → PET pathway.</p>

      {stats && (
        <div className="grid grid-4" style={{ marginBottom: 20 }}>
          <StatTile label="Patients in cohort" value={stats.total_patients} />
          <StatTile label="Critical priority" value={stats.by_urgency.critical} accent="var(--status-critical)" />
          <StatTile label="Reached PET stage" value={stats.stage_reach.pet} accent="var(--series-7)" />
          <StatTile label="Diagnostic resource saved" value={`${stats.estimated_resource_savings_pct}%`} accent="var(--status-good)" />
        </div>
      )}

      <div className="card" style={{ marginBottom: 20 }}>
        <h3>Priority Queue</h3>
        {!queue ? (
          <div className="empty-state">Loading…</div>
        ) : queue.length === 0 ? (
          <div className="empty-state">No patients yet. Add your first patient to get started.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Patient</th><th>Age</th><th>Urgency</th><th>Risk</th><th>Predicted</th><th>Last stage reached</th><th>Recommendation</th>
              </tr>
            </thead>
            <tbody>
              {queue.map(p => (
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

      <ModelCard />
    </div>
  )
}
