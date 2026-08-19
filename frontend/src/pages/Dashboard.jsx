import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getQueue, getQueueStats } from '../api'
import PriorityBadge from '../components/PriorityBadge'
import ModelCard from '../components/ModelCard'
import NeuralBrainCanvas from '../components/NeuralBrainCanvas'
import TiltCard from '../components/TiltCard'
import AnimatedNumber from '../components/AnimatedNumber'

const QUICK_ACTIONS = [
  { to: '/records', icon: '📋', label: 'Patient Records', desc: 'Browse and search the full triage queue' },
  { to: '/new', icon: '➕', label: 'New Patient', desc: 'Run a cognitive screening intake' },
  { to: '/optimize', icon: '⚙️', label: 'Resource Optimizer', desc: 'Allocate this week\'s CSF/MRI/PET slots' },
  { to: '/care', icon: '🏥', label: 'Care & Resources', desc: 'Nearby hospitals & emergency numbers' },
  { to: '/assistant', icon: '✦', label: 'AI Assistant', desc: 'Ask about Alzheimer\'s & dementia care' },
]

export default function Dashboard() {
  const [queue, setQueue] = useState(null)
  const [stats, setStats] = useState(null)

  useEffect(() => {
    getQueue().then(setQueue)
    getQueueStats().then(setStats)
  }, [])

  const needsAttention = (queue || []).filter(p => p.urgency === 'critical' || p.urgency === 'high').slice(0, 5)

  return (
    <div>
      <div className="page-banner">
        <svg className="ecg-line" viewBox="0 0 340 60" preserveAspectRatio="none">
          <path d="M0,30 L60,30 L75,10 L90,50 L105,30 L140,30 L150,18 L160,42 L170,30 L340,30" />
        </svg>
        <h1>Adaptive AI Triage for Early Alzheimer's Diagnosis</h1>
        <p className="subtitle">
          Every patient starts at cognitive screening. The model only escalates to CSF biomarkers,
          MRI, or PET when the evidence actually justifies the cost — so scarce imaging capacity goes
          to the patients who need it, not everyone.
        </p>
        <div className="banner-pills">
          <span className="banner-pill"><span className="dot" /> Cognitive: real OASIS data</span>
          <span className="banner-pill"><span className="dot" /> CSF: real biomarker cohort</span>
          <span className="banner-pill"><span className="dot" /> MRI: real OASIS data</span>
          <span className="banner-pill"><span className="dot" style={{ background: 'var(--text-muted)' }} /> PET: synthetic</span>
        </div>
      </div>

      {stats && (
        <div className="grid grid-4" style={{ marginBottom: 20 }}>
          <TiltCard className="card stat-tile">
            <div className="stat-value"><AnimatedNumber value={stats.total_patients} /></div>
            <div className="stat-label">Patients in cohort</div>
          </TiltCard>
          <TiltCard className="card stat-tile">
            <div className="stat-value" style={{ color: 'var(--status-critical)' }}><AnimatedNumber value={stats.by_urgency.critical} /></div>
            <div className="stat-label">Critical priority</div>
          </TiltCard>
          <TiltCard className="card stat-tile">
            <div className="stat-value" style={{ color: 'var(--series-7)' }}><AnimatedNumber value={stats.stage_reach.pet} /></div>
            <div className="stat-label">Reached PET stage</div>
          </TiltCard>
          <TiltCard className="card stat-tile">
            <div className="stat-value" style={{ color: 'var(--status-good)' }}><AnimatedNumber value={stats.estimated_resource_savings_pct} suffix="%" /></div>
            <div className="stat-label">Diagnostic resource saved</div>
          </TiltCard>
        </div>
      )}

      <div className="grid" style={{ gridTemplateColumns: '1.3fr 1fr', marginBottom: 20, alignItems: 'stretch' }}>
        <div className="card">
          <h3>Quick Actions</h3>
          <div className="grid grid-2" style={{ gap: 10 }}>
            {QUICK_ACTIONS.map(a => (
              <Link key={a.to} to={a.to} className="quick-action-tile">
                <span className="quick-action-icon">{a.icon}</span>
                <div>
                  <div className="quick-action-label">{a.label}</div>
                  <div className="field-hint">{a.desc}</div>
                </div>
              </Link>
            ))}
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4 }}>
            <h3 style={{ margin: 0 }}>Needs Attention</h3>
            <Link to="/records" className="field-hint">View all →</Link>
          </div>
          {!queue ? (
            <div className="empty-state">Loading…</div>
          ) : needsAttention.length === 0 ? (
            <div className="empty-state">No critical or high-urgency patients right now.</div>
          ) : (
            needsAttention.map(p => (
              <Link key={p.id} to={`/patients/${p.id}`} className="attention-row">
                <span>{p.name}</span>
                <PriorityBadge urgency={p.urgency} />
              </Link>
            ))
          )}
        </div>
      </div>

      <div className="viz-panel">
        <div className="viz-panel-head">
          <h3 style={{ margin: 0 }}>AI Reasoning Network</h3>
          <span className="field-hint">Procedural visualization of the stacked risk model — nodes represent the model's learned decision structure.</span>
        </div>
        <NeuralBrainCanvas height={220} />
      </div>

      <ModelCard />
    </div>
  )
}
