import { useEffect, useState } from 'react'
import { getModelCard, getSchema } from '../api'

const STAGE_LABEL = { cognitive: 'Cognitive', blood: 'Blood/CSF', mri: 'MRI', pet: 'PET' }
const SOURCE_LABEL = { real_oasis: 'Real — OASIS', real_csf: 'Real — CSF cohort', synthetic: 'Synthetic' }

function SourceBadge({ source }) {
  const isReal = source?.startsWith('real')
  return (
    <span className={`badge ${isReal ? 'badge-low' : 'badge-unassessed'}`}>
      <span className="badge-dot" />
      {SOURCE_LABEL[source] || source}
    </span>
  )
}

export default function ModelCard() {
  const [card, setCard] = useState(null)
  const [schema, setSchema] = useState(null)

  useEffect(() => {
    getModelCard().then(setCard).catch(() => {})
    getSchema().then(setSchema).catch(() => {})
  }, [])

  if (!card || !schema) return null

  return (
    <div className="card">
      <h3>Model Card</h3>
      <table style={{ marginBottom: 12 }}>
        <thead>
          <tr><th>Stage</th><th>Data source</th><th>Accuracy</th><th>Macro F1</th><th>ROC-AUC</th></tr>
        </thead>
        <tbody>
          {Object.entries(card.metrics).map(([stage, m]) => (
            <tr key={stage}>
              <td>{STAGE_LABEL[stage] || stage}</td>
              <td><SourceBadge source={schema.stage_data_source[stage]} /></td>
              <td>{(m.accuracy * 100).toFixed(1)}%</td>
              <td>{m.macro_f1.toFixed(3)}</td>
              <td>{m.roc_auc_ovr ? m.roc_auc_ovr.toFixed(3) : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="disclaimer">
        <strong>Data provenance:</strong> {card.data_provenance}
        <br /><br />
        <strong>Intended use:</strong> {card.intended_use}
      </div>
    </div>
  )
}
