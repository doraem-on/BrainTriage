import { useEffect, useState } from 'react'
import { geocode, getNearbyHospitals, getEmergencyNumbers } from '../api'

function mapsUrl(lat, lon) {
  return `https://www.google.com/maps/search/?api=1&query=${lat},${lon}`
}

function HospitalFinder() {
  const [query, setQuery] = useState('')
  const [candidates, setCandidates] = useState(null)
  const [center, setCenter] = useState(null)
  const [hospitals, setHospitals] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const searchHospitals = (lat, lon, label) => {
    setLoading(true)
    setError(null)
    setCenter({ lat, lon, label })
    setCandidates(null)
    getNearbyHospitals(lat, lon, 15)
      .then(setHospitals)
      .catch(() => setError('Could not reach the hospital lookup service (OpenStreetMap Overpass). Try again in a moment.'))
      .finally(() => setLoading(false))
  }

  const handleUseLocation = () => {
    if (!navigator.geolocation) {
      setError('Geolocation is not available in this browser.')
      return
    }
    setLoading(true)
    navigator.geolocation.getCurrentPosition(
      (pos) => searchHospitals(pos.coords.latitude, pos.coords.longitude, 'your location'),
      () => { setError('Location access was denied. Try searching by city instead.'); setLoading(false) },
      { timeout: 10000 }
    )
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    setError(null)
    setLoading(true)
    try {
      const results = await geocode(query)
      if (results.length === 0) {
        setError('No matching places found.')
        setLoading(false)
        return
      }
      if (results.length === 1) {
        searchHospitals(results[0].lat, results[0].lon, results[0].display_name)
      } else {
        setCandidates(results)
        setLoading(false)
      }
    } catch {
      setError('Geocoding service unavailable. Try again in a moment.')
      setLoading(false)
    }
  }

  return (
    <div className="card" style={{ marginBottom: 20 }}>
      <h3>Find Nearby Hospitals</h3>
      <p className="field-hint" style={{ marginBottom: 14 }}>
        Real hospital data via OpenStreetMap — no account or API key needed. Useful for
        routing a patient who's just been flagged high-risk to the nearest facility.
      </p>

      <div style={{ display: 'flex', gap: 10, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn btn-primary" onClick={handleUseLocation} disabled={loading}>
          📍 Use my location
        </button>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: 8, flex: 1, minWidth: 240 }}>
          <input
            placeholder="Search by city or address (e.g. Ranchi, Jharkhand)"
            value={query}
            onChange={e => setQuery(e.target.value)}
            style={{ flex: 1, padding: '9px 10px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--surface-2)', color: 'var(--text-primary)' }}
          />
          <button className="btn" type="submit" disabled={loading}>Search</button>
        </form>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {loading && <div className="empty-state">Searching…</div>}

      {candidates && (
        <div style={{ marginBottom: 14 }}>
          <div className="field-hint" style={{ marginBottom: 6 }}>Multiple matches — pick one:</div>
          {candidates.map((c, i) => (
            <div key={i} onClick={() => searchHospitals(c.lat, c.lon, c.display_name)}
                 style={{ padding: '8px 10px', borderRadius: 8, cursor: 'pointer', border: '1px solid var(--border)', marginBottom: 6 }}>
              {c.display_name}
            </div>
          ))}
        </div>
      )}

      {hospitals && (
        <>
          <div className="field-hint" style={{ marginBottom: 10 }}>
            {hospitals.length} facilities found near {center?.label} (15 km radius)
          </div>
          <table>
            <thead>
              <tr><th>Facility</th><th>Address</th><th>Distance</th><th></th></tr>
            </thead>
            <tbody>
              {hospitals.map((h, i) => (
                <tr key={i} style={{ cursor: 'default' }}>
                  <td><strong>{h.name}</strong>{h.emergency && <span className="badge badge-critical" style={{ marginLeft: 8 }}><span className="badge-dot" />ER</span>}</td>
                  <td className="field-hint">{h.address || '—'}</td>
                  <td>{h.distance_km} km</td>
                  <td><a href={mapsUrl(h.lat, h.lon)} target="_blank" rel="noreferrer" className="btn" style={{ padding: '4px 10px', fontSize: 12 }}>Directions</a></td>
                </tr>
              ))}
            </tbody>
          </table>
          {hospitals.length === 0 && <div className="empty-state">No hospitals found in this radius in OpenStreetMap's data — try a nearby city.</div>}
        </>
      )}
    </div>
  )
}

function EmergencyNumbers() {
  const [data, setData] = useState(null)
  const [country, setCountry] = useState('IN')

  useEffect(() => {
    getEmergencyNumbers().then(d => { setData(d); setCountry(d.default) })
  }, [])

  if (!data) return null
  const entry = data.countries[country]

  return (
    <div className="card">
      <h3>Emergency Numbers</h3>
      <div className="disclaimer" style={{ marginBottom: 14 }}>{data.disclaimer}</div>

      <div className="field" style={{ maxWidth: 260, marginBottom: 16 }}>
        <label>Country</label>
        <select value={country} onChange={e => setCountry(e.target.value)}>
          {Object.entries(data.countries).map(([code, c]) => (
            <option key={code} value={code}>{c.country}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-2">
        <div>
          <div className="field-hint" style={{ fontWeight: 700, marginBottom: 8 }}>GENERAL EMERGENCY</div>
          {entry.general.map((n, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--gridline)' }}>
              <span>{n.label}</span>
              <strong style={{ fontVariantNumeric: 'tabular-nums' }}>{n.number}</strong>
            </div>
          ))}
        </div>
        <div>
          <div className="field-hint" style={{ fontWeight: 700, marginBottom: 8 }}>DEMENTIA / ALZHEIMER'S SUPPORT</div>
          {entry.dementia_specific.length === 0 && <div className="empty-state" style={{ padding: 8 }}>No entry for this country yet.</div>}
          {entry.dementia_specific.map((n, i) => (
            <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--gridline)' }}>
              <span>{n.label}{n.verify && <span className="field-hint"> (verify locally)</span>}</span>
              <strong style={{ fontVariantNumeric: 'tabular-nums' }}>{n.number}</strong>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function CareResources() {
  return (
    <div>
      <h1>Care &amp; Emergency Resources</h1>
      <p className="subtitle">Real hospital locations and emergency contact numbers — for when a triage result needs to turn into an actual next step.</p>
      <HospitalFinder />
      <EmergencyNumbers />
    </div>
  )
}
