const STAGE_COLOR = {
  cognitive: 'var(--series-1)',
  blood: 'var(--series-2)',
  mri: 'var(--series-3)',
  pet: 'var(--series-7)',
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
            </div>
            {isDone ? (
              <>
                <div className="pipeline-stage-risk">{(r.risk_probability * 100).toFixed(0)}%</div>
                <div className="field-hint">
                  {r.escalated === null ? 'final stage' : r.escalated ? 'escalated ↑' : 'gated — monitor'}
                </div>
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
