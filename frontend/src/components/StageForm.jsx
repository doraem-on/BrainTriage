import { useState } from 'react'

export default function StageForm({ stage, features, featureLabels, onSubmit, submitting }) {
  const [values, setValues] = useState(() => Object.fromEntries(features.map(f => [f, ''])))

  const handleChange = (f, v) => setValues(prev => ({ ...prev, [f]: v }))

  const handleSubmit = (e) => {
    e.preventDefault()
    const payload = {}
    for (const f of features) {
      payload[f] = parseFloat(values[f])
    }
    onSubmit(payload)
  }

  const isValid = features.every(f => values[f] !== '' && !Number.isNaN(parseFloat(values[f])))

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-grid">
        {features.map(f => (
          <div className="field" key={f}>
            <label htmlFor={`${stage}-${f}`}>{featureLabels[f] || f}</label>
            {f === 'apoe4_alleles' ? (
              <select id={`${stage}-${f}`} value={values[f]} onChange={e => handleChange(f, e.target.value)} required>
                <option value="" disabled>select…</option>
                <option value="0">0</option>
                <option value="1">1</option>
                <option value="2">2</option>
              </select>
            ) : (
              <input
                id={`${stage}-${f}`}
                type="number"
                step="any"
                value={values[f]}
                onChange={e => handleChange(f, e.target.value)}
                required
              />
            )}
          </div>
        ))}
      </div>
      <div style={{ marginTop: 16 }}>
        <button type="submit" className="btn btn-primary" disabled={!isValid || submitting}>
          {submitting ? 'Submitting…' : 'Submit & Re-evaluate'}
        </button>
      </div>
    </form>
  )
}
