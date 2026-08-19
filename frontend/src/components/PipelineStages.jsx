const STAGE_COLOR = {
  cognitive: 'var(--series-1)',
  blood: 'var(--series-2)',
  mri: 'var(--series-3)',
  pet: 'var(--series-7)',
}

function statusText(r) {
  if (r.escalated === null) return 'final stage'
  if (r.escalated) return r.escalation_reason === 'low_confidence' ? 'escalated — low confidence ⚠' : 'escalated ↑'
  const dist = r.threshold_distance
  return dist != null ? `gated — ${Math.round(dist * 100)}% below threshold` : 'gated — monitor'
}

export default function PipelineStages({ stageOrder, stageLabels, stageResults }) {
  const byStage = Object.fromEntries((stageResults || []).map(s => [s.stage, s]))
  const lastIndex = stageResults?.length ? stageOrder.indexOf(stageResults[stageResults.length - 1].stage) : -1

  return (
    <div className="pipeline-track">
      {stageOrder.map((stage, i) => {
        const r = byStage[stage]
        const isDone = !!r
        const isGated = isDone && r.escalated === false
        const isPending = !isDone && i <= lastIndex + 1 && i === lastIndex + 1
        let cls = 'pipeline-stage '
        if (isDone) cls += isGated ? 'gated' : 'done'
        else if (isPending) cls += 'pending'
        else cls += 'gated'

        return (
          <div className="pipeline-stage" key={stage}
               style={{ borderColor: isDone && !isGated ? STAGE_COLOR[stage] : undefined, opacity: !isDone && !isPending ? 0.4 : undefined }}>
            <div className="pipeline-stage-label">
              <span className="legend-swatch" style={{ background: STAGE_COLOR[stage] }} />
              {stageLabels[stage]}
              {isDone && r.data_source === 'synthetic' && (
                <span title="Trained on synthetic data — no real dataset available for this stage" style={{ marginLeft: 4 }}>🧪</span>
              )}
            </div>
            {isDone ? (
              <>
                <div className="pipeline-stage-risk">{(r.risk_probability * 100).toFixed(0)}%</div>
                <div className="field-hint">{statusText(r)}</div>
                {r.abstain && (
                  <div className="field-hint" style={{ color: 'var(--status-warning)', fontWeight: 700, marginTop: 3 }}>
                    ⚠ Low confidence ({(r.confidence_margin * 100).toFixed(0)}% margin)
                  </div>
                )}
              </>
            ) : isPending ? (
              <div className="field-hint">awaiting data entry</div>
            ) : (
              <div className="field-hint">not reached</div>
            )}
          </div>
        )
      })}
    </div>
  )
}
