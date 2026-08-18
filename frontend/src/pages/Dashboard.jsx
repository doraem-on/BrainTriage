import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { getQueue, getQueueStats } from '../api'
import PriorityBadge from '../components/PriorityBadge'
import ModelCard from '../components/ModelCard'
import NeuralBrainCanvas from '../components/NeuralBrainCanvas'
import TiltCard from '../components/TiltCard'

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
      <div className="hero-card">
        <div className="hero-copy">
          <div className="hero-eyebrow"><span className="dot" /> Live triage engine</div>
          <h1>Adaptive AI Triage for Early Alzheimer's Diagnosis</h1>
          <p className="subtitle" style={{ marginBottom: 18 }}>
            Every patient starts at cognitive screening. The model only escalates to CSF biomarkers,
            MRI, or PET when the evidence actually justifies the cost — so scarce imaging capacity goes
            to the patients who need it, not everyone.
          </p>
          <div className="source-strip">
            <span className="source-chip"><span className="dot" style={{ background: 'var(--status-good)' }} /> Cognitive: real OASIS data</span>
            <span className="source-chip"><span className="dot" style={{ background: 'var(--status-good)' }} /> CSF: real biomarker cohort</span>
            <span className="source-chip"><span className="dot" style={{ background: 'var(--status-good)' }} /> MRI: real OASIS data</span>
            <span className="source-chip"><span className="dot" style={{ background: 'var(--text-muted)' }} /> PET: synthetic</span>
          </div>
        </div>
        <div className="hero-viz">
          <NeuralBrainCanvas height={300} />
        </div>
      </div>

      {stats && (
        <div className="grid grid-4" style={{ marginBottom: 20 }}>
          <TiltCard className="card stat-tile">
            <div className="stat-value">{stats.total_patients}</div>
            <div className="stat-label">Patients in cohort</div>
          </TiltCard>
          <TiltCard className="card stat-tile">
            <div className="stat-value" style={{ color: 'var(--status-critical)' }}>{stats.by_urgency.critical}</div>
            <div className="stat-label">Critical priority</div>
          </TiltCard>
          <TiltCard className="card stat-tile">
            <div className="stat-value" style={{ color: 'var(--series-7)' }}>{stats.stage_reach.pet}</div>
            <div className="stat-label">Reached PET stage</div>
          </TiltCard>
          <TiltCard className="card stat-tile">
            <div className="stat-value" style={{ color: 'var(--status-good)' }}>{stats.estimated_resource_savings_pct}%</div>
            <div className="stat-label">Diagnostic resource saved</div>
          </TiltCard>
        </div>
      )}

      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0 }}>Priority Queue</h3>
          <Link to="/optimize" className="btn" style={{ fontSize: 12.5 }}>Plan this week's capacity →</Link>
        </div>
        <div style={{ height: 8 }} />
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
