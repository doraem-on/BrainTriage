import { useEffect, useState } from 'react'
import { getImpact } from '../api'

const STAGE_LABEL = { cognitive: 'Cognitive', blood: 'CSF Biomarkers', mri: 'MRI', pet: 'PET' }
const STAGE_ORDER = ['cognitive', 'blood', 'mri', 'pet']

function FunnelRow({ stage, traditional, actual, total }) {
  const pct = total ? Math.round((actual / total) * 100) : 0
  return (
    <div style={{ marginBottom: 18 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, fontWeight: 600, marginBottom: 6 }}>
        <span>{STAGE_LABEL[stage]}</span>
        <span className="field-hint">{actual} of {total} patients ({pct}%)</span>
      </div>
      <div style={{ position: 'relative', height: 22, background: 'var(--gridline)', borderRadius: 8, overflow: 'hidden' }}>
        <div style={{ position: 'absolute', inset: 0, width: '100%', background: 'var(--text-muted)', opacity: 0.25 }} />
        <div style={{
          position: 'absolute', top: 0, bottom: 0, left: 0,
          width: `${pct}%`, background: 'linear-gradient(90deg, var(--brand-primary), var(--brand-accent))',
          borderRadius: 8, transition: 'width 0.6s ease',
        }} />
      </div>
    </div>
  )
}

export default function ImpactDashboard() {
  const [data, setData] = useState(null)

  useEffect(() => { getImpact().then(setData) }, [])

  if (!data) return <div className="empty-state">Loading…</div>
  if (data.total_patients === 0) {
    return (
      <div>
        <h1>BrainTriage Impact</h1>
        <p className="subtitle">Add some patients first — this compares the traditional "everyone gets every test" pathway against what BrainTriage's adaptive gating actually ran.</p>
      </div>
    )
  }

  return (
    <div>
      <h1>BrainTriage Impact</h1>
      <p className="subtitle">
        Traditional diagnostic pathways run every patient through every test. BrainTriage only
        escalates when the evidence justifies it. Here's the difference, measured on this cohort.
      </p>
      <div className="disclaimer" style={{ marginBottom: 20 }}>{data.disclaimer}</div>

      <div className="grid grid-2" style={{ marginBottom: 20 }}>
        <div className="card">
          <h3>Traditional Pathway</h3>
          <p className="field-hint" style={{ marginBottom: 14 }}>Every patient receives every test, regardless of risk.</p>
          {STAGE_ORDER.map(s => (
            <FunnelRow key={s} stage={s} actual={data.traditional[s]} total={data.total_patients} />
          ))}
        </div>
        <div className="card">
          <h3>BrainTriage Adaptive Pathway</h3>
          <p className="field-hint" style={{ marginBottom: 14 }}>Only patients whose risk crossed the escalation threshold proceed.</p>
          {STAGE_ORDER.map(s => (
            <FunnelRow key={s} stage={s} actual={data.braintriage[s]} total={data.total_patients} />
          ))}
        </div>
      </div>

      <div className="grid grid-4" style={{ marginBottom: 20 }}>
        <div className="card stat-tile">
          <div className="stat-value" style={{ color: 'var(--status-good)' }}>{data.diagnostic_burden_reduction_pct}%</div>
          <div className="stat-label">Diagnostic burden reduction</div>
        </div>
        <div className="card stat-tile">
          <div className="stat-value">{data.tests_avoided.blood}</div>
          <div className="stat-label">CSF panels avoided</div>
        </div>
        <div className="card stat-tile">
          <div className="stat-value">{data.tests_avoided.mri}</div>
          <div className="stat-label">MRI scans avoided</div>
        </div>
        <div className="card stat-tile">
          <div className="stat-value">{data.tests_avoided.pet}</div>
          <div className="stat-label">PET scans avoided</div>
        </div>
      </div>

      <div className="card">
        <h3>Cost Units</h3>
        <p className="field-hint" style={{ marginBottom: 10 }}>
          A relative cost/invasiveness score per stage (Cognitive=1, CSF=6, MRI=12, PET=40) — not a real
          currency figure, just a way to compare diagnostic burden across the two pathways.
        </p>
        <div style={{ display: 'flex', gap: 24 }}>
          <div><div className="stat-value" style={{ fontSize: 22 }}>{data.traditional_cost_units}</div><div className="stat-label">Traditional</div></div>
          <div><div className="stat-value" style={{ fontSize: 22, color: 'var(--brand-primary)' }}>{data.braintriage_cost_units}</div><div className="stat-label">BrainTriage</div></div>
        </div>
      </div>
    </div>
  )
}
