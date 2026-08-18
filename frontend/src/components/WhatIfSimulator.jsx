import { useEffect, useRef, useState } from 'react'
import { simulatePatient } from '../api'
import PriorityBadge from './PriorityBadge'

const SLIDER_CONFIG = {
  age: { min: 55, max: 95, step: 1 },
  education_years: { min: 0, max: 20, step: 1 },
  ses: { min: 1, max: 5, step: 1 },
  sex_male: { min: 0, max: 1, step: 1, binary: 'Sex: Male' },
  mmse_score: { min: 0, max: 30, step: 1 },
  apoe4_positive: { min: 0, max: 1, step: 1, binary: 'APOE4 Positive' },
  csf_amyloid: { min: 200, max: 1000, step: 10 },
  csf_ttau: { min: 100, max: 700, step: 10 },
  csf_ptau: { min: 20, max: 250, step: 5 },
  etiv: { min: 1100, max: 2100, step: 10 },
  nwbv: { min: 0.6, max: 0.85, step: 0.005 },
  asf: { min: 0.85, max: 1.6, step: 0.01 },
  amyloid_suvr: { min: 0.8, max: 2.2, step: 0.02 },
  tau_suvr: { min: 0.8, max: 2.6, step: 0.02 },
  fdg_suvr: { min: 0.85, max: 1.6, step: 0.02 },
}

export default function WhatIfSimulator({ patientId, stage, stageLabel, featureLabels, inputs }) {
  const [values, setValues] = useState(inputs)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const debounceRef = useRef(null)

  useEffect(() => { setValues(inputs) }, [inputs])

  const runSim = (nextValues) => {
    setLoading(true)
    simulatePatient(patientId, nextValues)
      .then(setResult)
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  const handleChange = (feature, raw) => {
    const next = { ...values, [feature]: parseFloat(raw) }
    setValues(next)
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => runSim(next), 220)
  }

  const handleReset = () => {
    setValues(inputs)
    setResult(null)
  }

  const baseline = result || { final_risk_probability: null }
  const features = Object.keys(inputs)

  return (
    <div>
      <p className="field-hint" style={{ marginBottom: 16 }}>
        Drag a slider to see how the {stageLabel.toLowerCase()} model's risk estimate would change —
        nothing here is saved to the patient record.
      </p>
      <div className="grid grid-2">
        <div>
          {features.map(f => {
            const cfg = SLIDER_CONFIG[f] || { min: 0, max: (values[f] || 1) * 2, step: 0.1 }
            const val = values[f]
            if (cfg.binary) {
              return (
                <div className="slider-row" key={f}>
                  <div className="slider-head"><span>{cfg.binary}</span></div>
                  <select value={val} onChange={e => handleChange(f, e.target.value)}
                          style={{ padding: '7px 9px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--surface-2)', color: 'var(--text-primary)' }}>
                    <option value={0}>No</option>
                    <option value={1}>Yes</option>
                  </select>
                </div>
              )
            }
            return (
              <div className="slider-row" key={f}>
                <div className="slider-head">
                  <span>{featureLabels[f] || f}</span>
                  <strong>{Number(val).toLocaleString(undefined, { maximumFractionDigits: 3 })}</strong>
                </div>
                <input
                  type="range"
                  min={cfg.min} max={cfg.max} step={cfg.step}
                  value={val}
                  onChange={e => handleChange(f, e.target.value)}
                />
              </div>
            )
          })}
          <button className="btn" onClick={handleReset} style={{ marginTop: 4 }}>Reset to recorded values</button>
        </div>

        <div className="card" style={{ background: 'var(--surface-2)', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', gap: 10 }}>
          <div className="stat-label">SIMULATED RISK</div>
          <div className="stat-value" style={{ fontSize: 44, color: loading ? 'var(--text-muted)' : 'var(--series-1)' }}>
            {baseline.final_risk_probability != null ? `${(baseline.final_risk_probability * 100).toFixed(0)}%` : '—'}
          </div>
          {result && <PriorityBadge urgency={result.urgency} />}
          {result && <div className="field-hint" style={{ textAlign: 'center', maxWidth: 260 }}>{result.recommendation}</div>}
          {!result && <div className="field-hint">Move a slider to simulate</div>}
        </div>
      </div>
    </div>
  )
}
