import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createPatient } from '../api'

const CDR_OPTIONS = [0, 0.5, 1, 2, 3]

export default function NewPatient() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    external_id: '', name: '', age: '', sex: 'unspecified', education_years: '',
    moca_score: '', mmse_score: '', cdr_global: '0', cdr_sob: '',
    family_history: false, memory_complaint: false,
  })
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const set = (k, v) => setForm(prev => ({ ...prev, [k]: v }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      const payload = {
        external_id: form.external_id,
        name: form.name,
        age: parseFloat(form.age),
        sex: form.sex,
        education_years: form.education_years ? parseFloat(form.education_years) : null,
        cognitive: {
          moca_score: parseFloat(form.moca_score),
          mmse_score: parseFloat(form.mmse_score),
          cdr_global: parseFloat(form.cdr_global),
          cdr_sob: parseFloat(form.cdr_sob),
          family_history: form.family_history ? 1 : 0,
          memory_complaint: form.memory_complaint ? 1 : 0,
        },
      }
      const patient = await createPatient(payload)
      navigate(`/patients/${patient.id}`)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to create patient.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <h1>New Patient Intake</h1>
      <p className="subtitle">Stage 1 — Cognitive Screening. The AI will score risk immediately and recommend whether to proceed to blood biomarkers.</p>

      {error && <div className="error-banner">{error}</div>}

      <form onSubmit={handleSubmit} className="card">
        <h3>Demographics</h3>
        <div className="form-grid" style={{ marginBottom: 20 }}>
          <div className="field">
            <label>Patient / MRN ID</label>
            <input value={form.external_id} onChange={e => set('external_id', e.target.value)} required />
          </div>
          <div className="field">
            <label>Full name</label>
            <input value={form.name} onChange={e => set('name', e.target.value)} required />
          </div>
          <div className="field">
            <label>Age</label>
            <input type="number" min="18" max="110" value={form.age} onChange={e => set('age', e.target.value)} required />
          </div>
          <div className="field">
            <label>Sex</label>
            <select value={form.sex} onChange={e => set('sex', e.target.value)}>
              <option value="unspecified">Unspecified</option>
              <option value="female">Female</option>
              <option value="male">Male</option>
            </select>
          </div>
          <div className="field">
            <label>Education (years)</label>
            <input type="number" step="0.5" value={form.education_years} onChange={e => set('education_years', e.target.value)} />
          </div>
        </div>

        <h3>Cognitive Screening</h3>
        <div className="form-grid">
          <div className="field">
            <label>MoCA score (0–30)</label>
            <input type="number" min="0" max="30" value={form.moca_score} onChange={e => set('moca_score', e.target.value)} required />
          </div>
          <div className="field">
            <label>MMSE score (0–30)</label>
            <input type="number" min="0" max="30" value={form.mmse_score} onChange={e => set('mmse_score', e.target.value)} required />
          </div>
          <div className="field">
            <label>CDR Global</label>
            <select value={form.cdr_global} onChange={e => set('cdr_global', e.target.value)}>
              {CDR_OPTIONS.map(v => <option key={v} value={v}>{v}</option>)}
            </select>
          </div>
          <div className="field">
            <label>CDR Sum of Boxes (0–18)</label>
            <input type="number" min="0" max="18" step="0.5" value={form.cdr_sob} onChange={e => set('cdr_sob', e.target.value)} required />
          </div>
          <div className="field">
            <label>
              <input type="checkbox" checked={form.family_history} onChange={e => set('family_history', e.target.checked)} style={{ marginRight: 6 }} />
              Family history of Alzheimer's
            </label>
          </div>
          <div className="field">
            <label>
              <input type="checkbox" checked={form.memory_complaint} onChange={e => set('memory_complaint', e.target.checked)} style={{ marginRight: 6 }} />
              Subjective memory complaint
            </label>
          </div>
        </div>

        <div style={{ marginTop: 20 }}>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Evaluating…' : 'Run Cognitive Risk Assessment'}
          </button>
        </div>
      </form>
    </div>
  )
}
