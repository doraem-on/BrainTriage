import { useEffect, useState } from 'react'
import { getModelCard } from '../api'

const STAGE_LABEL = { cognitive: 'Cognitive', blood: 'Blood', mri: 'MRI', pet: 'PET' }

export default function ModelCard() {
  const [card, setCard] = useState(null)

  useEffect(() => { getModelCard().then(setCard).catch(() => {}) }, [])

  if (!card) return null

  return (
    <div className="card">
      <h3>Model Card</h3>
      <table style={{ marginBottom: 12 }}>
        <thead>
          <tr><th>Stage</th><th>Accuracy</th><th>Macro F1</th><th>ROC-AUC</th></tr>
        </thead>
        <tbody>
          {Object.entries(card.metrics).map(([stage, m]) => (
            <tr key={stage}>
              <td>{STAGE_LABEL[stage] || stage}</td>
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
