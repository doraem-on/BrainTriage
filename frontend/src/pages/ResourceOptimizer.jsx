import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getOptimize } from '../api'
import PriorityBadge from '../components/PriorityBadge'
import TiltCard from '../components/TiltCard'

const STAGE_COLOR = { blood: 'var(--series-2)', mri: 'var(--series-3)', pet: 'var(--series-7)' }

function StageColumn({ stageKey, data }) {
  const navigate = useNavigate()
  if (!data) return null
  return (
    <TiltCard className="card" maxTilt={4}>
      <div style={{ borderTop: `3px solid ${STAGE_COLOR[stageKey]}`, margin: '-20px -22px 16px', borderRadius: '20px 20px 0 0' }} />
      <h3>{data.stage_label}</h3>
      <div style={{ display: 'flex', gap: 18, marginBottom: 14 }}>
        <div>
          <div className="stat-value" style={{ fontSize: 22 }}>{data.slots_available}</div>
          <div className="stat-label">slots this week</div>
        </div>
        <div>
          <div className="stat-value" style={{ fontSize: 22 }}>{data.candidates_waiting}</div>
          <div className="stat-label">awaiting this test</div>
        </div>
      </div>

      {data.scheduled.length > 0 && (
        <>
          <div className="field-hint" style={{ marginBottom: 6, fontWeight: 700, color: 'var(--status-good)' }}>SCHEDULED</div>
          {data.scheduled.map(c => (
            <div key={c.id} onClick={() => navigate(`/patients/${c.id}`)}
                 style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px solid var(--gridline)', cursor: 'pointer' }}>
              <span>{c.name}</span>
              <PriorityBadge urgency={c.urgency} />
            </div>
          ))}
        </>
      )}

      {data.waitlisted.length > 0 && (
        <>
          <div className="field-hint" style={{ margin: '12px 0 6px', fontWeight: 700 }}>WAITLISTED</div>
          {data.waitlisted.map(c => (
            <div key={c.id} onClick={() => navigate(`/patients/${c.id}`)}
                 style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px solid var(--gridline)', opacity: 0.65, cursor: 'pointer' }}>
              <span>{c.name}</span>
              <PriorityBadge urgency={c.urgency} />
            </div>
          ))}
        </>
      )}

      {data.candidates_waiting === 0 && <div className="empty-state">No patients currently awaiting this test.</div>}
    </TiltCard>
  )
}

export default function ResourceOptimizer() {
  const [slots, setSlots] = useState({ blood_slots: 3, mri_slots: 2, pet_slots: 1 })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const load = (s) => {
    setLoading(true)
    getOptimize(s).then(setResult).finally(() => setLoading(false))
  }

  useEffect(() => { load(slots) }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const set = (k, v) => setSlots(prev => ({ ...prev, [k]: Math.max(0, parseInt(v) || 0) }))

  return (
    <div>
      <h1>Diagnostic Resource Optimizer</h1>
      <p className="subtitle">
        Real hospitals don't have unlimited MRI or PET capacity. Tell it how many slots you have this
        week for each test, and it ranks the patients actually awaiting that test by AI-estimated risk —
        so scarce capacity goes to whoever benefits most, not whoever was referred first.
      </p>

      <div className="card" style={{ marginBottom: 22 }}>
        <div className="form-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
          <div className="field">
            <label>CSF biomarker slots this week</label>
            <input type="number" min="0" value={slots.blood_slots} onChange={e => set('blood_slots', e.target.value)} />
          </div>
          <div className="field">
            <label>MRI slots this week</label>
            <input type="number" min="0" value={slots.mri_slots} onChange={e => set('mri_slots', e.target.value)} />
          </div>
          <div className="field">
            <label>PET slots this week</label>
            <input type="number" min="0" value={slots.pet_slots} onChange={e => set('pet_slots', e.target.value)} />
          </div>
        </div>
        <div style={{ marginTop: 16 }}>
          <button className="btn btn-primary" onClick={() => load(slots)} disabled={loading}>
            {loading ? 'Optimizing…' : 'Recalculate Allocation'}
          </button>
        </div>
      </div>

      {result && (
        <div className="grid" style={{ gridTemplateColumns: '1fr 1fr 1fr' }}>
          <StageColumn stageKey="blood" data={result.blood} />
          <StageColumn stageKey="mri" data={result.mri} />
          <StageColumn stageKey="pet" data={result.pet} />
        </div>
      )}
    </div>
  )
}
