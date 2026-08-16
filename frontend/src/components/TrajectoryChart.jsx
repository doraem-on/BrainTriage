import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Dot } from 'recharts'

function fmtDate(iso) {
  const d = new Date(iso)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const p = payload[0].payload
  return (
    <div className="card" style={{ padding: '8px 12px', fontSize: 12 }}>
      <div style={{ fontWeight: 700, marginBottom: 2 }}>{fmtDate(label)}</div>
      <div>Risk: {(p.final_risk_probability * 100).toFixed(1)}%</div>
      <div style={{ color: 'var(--text-muted)' }}>{p.predicted_class} · {p.last_stage}</div>
    </div>
  )
}

export default function TrajectoryChart({ history }) {
  if (!history?.length) return <div className="empty-state">No assessment history yet.</div>
  if (history.length === 1) {
    return <div className="empty-state">Only one assessment so far — trajectory appears after a follow-up evaluation.</div>
  }

  const data = history.map(h => ({ ...h, x: h.evaluated_at }))

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 8, right: 16, left: -12, bottom: 0 }}>
        <CartesianGrid stroke="var(--gridline)" vertical={false} />
        <XAxis dataKey="x" tickFormatter={fmtDate} tick={{ fontSize: 11, fill: 'var(--text-muted)' }} stroke="var(--baseline)" />
        <YAxis domain={[0, 1]} tickFormatter={(v) => `${Math.round(v * 100)}%`} tick={{ fontSize: 11, fill: 'var(--text-muted)' }} stroke="var(--baseline)" width={44} />
        <Tooltip content={<CustomTooltip />} />
        <Line
          type="monotone"
          dataKey="final_risk_probability"
          stroke="var(--series-1)"
          strokeWidth={2}
          dot={{ r: 4, fill: 'var(--series-1)', strokeWidth: 0 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
