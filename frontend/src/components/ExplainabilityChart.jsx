export default function ExplainabilityChart({ contributors }) {
  if (!contributors?.length) return <div className="empty-state">No contributor data.</div>

  const maxAbs = Math.max(...contributors.map(c => Math.abs(c.contribution)), 0.0001)

  return (
    <div>
      {contributors.map((c) => {
        const pct = (Math.abs(c.contribution) / maxAbs) * 50 // half-track since bar grows from center
        const isRisk = c.contribution >= 0
        return (
          <div className="contrib-row" key={c.feature}>
            <div className="contrib-label" title={c.label}>{c.label}</div>
            <div className="contrib-bar-track">
              <div
                className="contrib-bar-fill"
                style={{
                  left: isRisk ? '50%' : `${50 - pct}%`,
                  width: `${pct}%`,
                  background: isRisk ? 'var(--status-critical)' : 'var(--series-1)',
                }}
              />
            </div>
            <div className="contrib-value">{c.value.toFixed(2)}</div>
          </div>
        )
      })}
      <div className="legend-row" style={{ marginTop: 10 }}>
        <span><span className="legend-swatch" style={{ background: 'var(--status-critical)' }} />Increases risk</span>
        <span><span className="legend-swatch" style={{ background: 'var(--series-1)' }} />Decreases risk</span>
      </div>
    </div>
  )
}
