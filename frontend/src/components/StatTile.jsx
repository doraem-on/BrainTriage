export default function StatTile({ label, value, accent }) {
  return (
    <div className="card stat-tile">
      <div className="stat-value" style={accent ? { color: accent } : undefined}>{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  )
}
