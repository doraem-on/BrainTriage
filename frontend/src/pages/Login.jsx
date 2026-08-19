import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth'
import NeuralBrainCanvas from '../components/NeuralBrainCanvas'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const from = location.state?.from || '/'

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(username, password)
      navigate(from, { replace: true })
    } catch {
      setError('Invalid username or password.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="login-screen">
      <div className="login-visual">
        <NeuralBrainCanvas height={340} nodeColor={0x5b93e8} edgeColor={0x1958c9} />
        <div className="login-visual-copy">
          <h2 style={{ color: 'white', textTransform: 'none', letterSpacing: 0, fontSize: 20 }}>BrainTriage</h2>
          <p>Adaptive AI triage for early Alzheimer's diagnostic pathways.</p>
        </div>
      </div>
      <div className="login-panel">
        <div className="login-card">
          <h1 style={{ marginBottom: 6 }}>Clinician Sign In</h1>
          <p className="subtitle">Restricted to authorized care team members.</p>

          {error && <div className="error-banner">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="field" style={{ marginBottom: 14 }}>
              <label>Username</label>
              <input value={username} onChange={e => setUsername(e.target.value)} autoFocus required />
            </div>
            <div className="field" style={{ marginBottom: 20 }}>
              <label>Password</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} required />
            </div>
            <button className="btn btn-primary" type="submit" style={{ width: '100%', justifyContent: 'center' }} disabled={submitting}>
              {submitting ? 'Signing in…' : 'Sign In'}
            </button>
          </form>

          <div className="disclaimer" style={{ marginTop: 20 }}>
            Demo credentials: <code>admin</code> / <code>braintriage2026</code> (change in backend/.env before any real use).
            Looking for hospital locations or emergency numbers? <a href="/care">Care &amp; Resources</a> is open without sign-in.
          </div>
        </div>
      </div>
    </div>
  )
}
