import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getPatient, getSchema, getHistory, submitStage, deletePatient, reportUrl } from '../api'
import PipelineStages from '../components/PipelineStages'
import ExplainabilityChart from '../components/ExplainabilityChart'
import TrajectoryChart from '../components/TrajectoryChart'
import StageForm from '../components/StageForm'
import PriorityBadge from '../components/PriorityBadge'
import WhatIfSimulator from '../components/WhatIfSimulator'

export default function PatientDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [patient, setPatient] = useState(null)
  const [schema, setSchema] = useState(null)
  const [history, setHistory] = useState(null)
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const [tab, setTab] = useState('overview')

  const load = useCallback(() => {
    getPatient(id).then(setPatient).catch(() => setError('Patient not found.'))
    getHistory(id).then(setHistory)
  }, [id])

  useEffect(() => { getSchema().then(setSchema) }, [])
  useEffect(load, [load])

  if (error) return <div className="error-banner">{error}</div>
  if (!patient || !schema) return <div className="empty-state">Loading…</div>

  const result = patient.last_result
  const lastStageResult = result?.stage_results?.[result.stage_results.length - 1]
  const lastStageIdx = schema.stage_order.indexOf(result?.last_stage)
  const nextStage = lastStageResult?.escalated === true ? schema.stage_order[lastStageIdx + 1] : null

  const handleStageSubmit = async (data) => {
    setSubmitting(true)
    setError(null)
    try {
      await submitStage(id, nextStage, data)
      load()
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to submit stage data.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async () => {
    if (!window.confirm(`Remove ${patient.name} from the cohort?`)) return
    await deletePatient(id)
    navigate('/')
  }

  return (
    <div>
      <Link to="/" className="field-hint">← Back to dashboard</Link>
      <h1 style={{ marginTop: 8 }}>{patient.name}</h1>
      <p className="subtitle">
        {patient.external_id} · Age {patient.age} · {patient.sex}
        {result && <> &nbsp;·&nbsp; <PriorityBadge urgency={result.urgency} /></>}
      </p>

      {error && <div className="error-banner">{error}</div>}

      {result && (
        <div className="card" style={{ marginBottom: 20 }}>
          <h3>Diagnostic Pathway</h3>
          <PipelineStages stageOrder={schema.stage_order} stageLabels={schema.stage_labels} stageResults={result.stage_results} />
          {lastStageResult?.narrative && (
            <div className="narrative-box" style={{ marginTop: 14 }}>{lastStageResult.narrative}</div>
          )}
          <div style={{ marginTop: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
            <div>
              <strong>{result.predicted_class}</strong> · risk {(result.final_risk_probability * 100).toFixed(0)}% ·
              <span className="field-hint"> {result.recommendation}</span>
            </div>
            <a className="btn" href={reportUrl(id)} target="_blank" rel="noreferrer">Download PDF report</a>
          </div>
        </div>
      )}

      {nextStage && (
        <div className="card" style={{ marginBottom: 20 }}>
          <h3>Escalate to {schema.stage_labels[nextStage]}</h3>
          <p className="field-hint" style={{ marginBottom: 12 }}>
            Cumulative risk crossed the {schema.stage_labels[result.last_stage]} escalation threshold
            ({Math.round(lastStageResult.threshold * 100)}%). Enter {schema.stage_labels[nextStage].toLowerCase()} results to refine the assessment.
          </p>
          <StageForm
            stage={nextStage}
            features={schema.stage_features[nextStage]}
            featureLabels={schema.feature_labels}
            onSubmit={handleStageSubmit}
            submitting={submitting}
          />
        </div>
      )}

      <div className="tabbar">
        <button className={tab === 'overview' ? 'active' : ''} onClick={() => setTab('overview')}>Explainability</button>
        <button className={tab === 'whatif' ? 'active' : ''} onClick={() => setTab('whatif')}>What-If Simulator</button>
        <button className={tab === 'trajectory' ? 'active' : ''} onClick={() => setTab('trajectory')}>Trajectory</button>
      </div>

      {tab === 'overview' && lastStageResult && (
        <div className="card" style={{ marginBottom: 20 }}>
          <h3>Top Contributing Factors — {schema.stage_labels[lastStageResult.stage]} stage</h3>
          <ExplainabilityChart contributors={lastStageResult.top_contributors} />
        </div>
      )}

      {tab === 'whatif' && lastStageResult && (
        <div className="card" style={{ marginBottom: 20 }}>
          <h3>What-If Simulator — {schema.stage_labels[lastStageResult.stage]} stage</h3>
          <WhatIfSimulator
            patientId={id}
            stage={lastStageResult.stage}
            stageLabel={schema.stage_labels[lastStageResult.stage]}
            featureLabels={schema.feature_labels}
            inputs={lastStageResult.inputs}
          />
        </div>
      )}

      {tab === 'trajectory' && (
        <div className="card" style={{ marginBottom: 20 }}>
          <h3>Risk Trajectory Over Time</h3>
          <TrajectoryChart history={history} />
        </div>
      )}

      <button className="btn" style={{ color: 'var(--status-critical)' }} onClick={handleDelete}>Remove patient</button>
    </div>
  )
}
