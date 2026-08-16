export default function PriorityBadge({ urgency }) {
  const label = {
    critical: 'Critical',
    high: 'High',
    moderate: 'Moderate',
    low: 'Low',
    unassessed: 'Unassessed',
  }[urgency] || urgency

  return (
    <span className={`badge badge-${urgency}`}>
      <span className="badge-dot" />
      {label}
    </span>
  )
}
