import { Routes, Route, Navigate, NavLink, Link, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import PatientRecords from './pages/PatientRecords'
import NewPatient from './pages/NewPatient'
import PatientDetail from './pages/PatientDetail'
import ResourceOptimizer from './pages/ResourceOptimizer'
import CareResources from './pages/CareResources'
import AIAssistant from './pages/AIAssistant'
import ImpactDashboard from './pages/ImpactDashboard'
import Login from './pages/Login'
import { AuthProvider, useAuth } from './auth'

function BackgroundBlobs() {
  return (
    <div className="bg-blobs" aria-hidden="true">
      <div className="bg-blob b1" />
      <div className="bg-blob b2" />
      <div className="bg-blob b3" />
    </div>
  )
}

function RequireAuth({ children }) {
  const { isAuthenticated, checking } = useAuth()
  const location = useLocation()
  if (checking) return null
  if (!isAuthenticated) return <Navigate to="/login" state={{ from: location.pathname }} replace />
  return children
}

function Shell() {
  const { logout, username } = useAuth()
  return (
    <div className="app-root">
      <header className="topbar">
        <Link to="/" className="topbar-brand">
          <span className="topbar-mark">B</span>
          <span className="topbar-word">BrainTriage</span>
          <span className="topbar-tag">Precision Care Challenge 2026</span>
        </Link>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div className="topbar-status">
            <span className="dot" /> 3 of 4 stages trained on real published data
          </div>
          {username && (
            <button className="topbar-logout" onClick={logout}>{username} · Sign out</button>
          )}
        </div>
      </header>

      <div className="safety-gate">
        ⚠ Decision-support only — not an autonomous diagnosis. Every recommendation requires clinician review, acceptance, or override before it's acted on.
      </div>

      <div className="app-shell">
        <aside className="sidebar">
          <nav className="nav-links">
            <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>
              <span className="nav-icon">◆</span> Dashboard
            </NavLink>
            <NavLink to="/records" className={({ isActive }) => isActive ? 'active' : ''}>
              <span className="nav-icon">📋</span> Patient Records
            </NavLink>
            <NavLink to="/new" className={({ isActive }) => isActive ? 'active' : ''}>
              <span className="nav-icon">＋</span> New Patient
            </NavLink>
            <NavLink to="/optimize" className={({ isActive }) => isActive ? 'active' : ''}>
              <span className="nav-icon">⚙</span> Resource Optimizer
            </NavLink>
            <NavLink to="/impact" className={({ isActive }) => isActive ? 'active' : ''}>
              <span className="nav-icon">📈</span> Impact Dashboard
            </NavLink>
            <NavLink to="/care" className={({ isActive }) => isActive ? 'active' : ''}>
              <span className="nav-icon">✚</span> Care &amp; Resources
            </NavLink>
            <NavLink to="/assistant" className={({ isActive }) => isActive ? 'active' : ''}>
              <span className="nav-icon">✦</span> AI Assistant
            </NavLink>
          </nav>
          <div className="sidebar-footer">
            <strong>Adaptive AI triage</strong> for early Alzheimer's diagnostic pathways.<br /><br />
            Research/hackathon prototype — not a validated diagnostic device.
          </div>
        </aside>
        <main className="main">
          <Routes>
            <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
            <Route path="/records" element={<RequireAuth><PatientRecords /></RequireAuth>} />
            <Route path="/new" element={<RequireAuth><NewPatient /></RequireAuth>} />
            <Route path="/optimize" element={<RequireAuth><ResourceOptimizer /></RequireAuth>} />
            <Route path="/impact" element={<RequireAuth><ImpactDashboard /></RequireAuth>} />
            <Route path="/care" element={<CareResources />} />
            <Route path="/assistant" element={<RequireAuth><AIAssistant /></RequireAuth>} />
            <Route path="/patients/:id" element={<RequireAuth><PatientDetail /></RequireAuth>} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BackgroundBlobs />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/*" element={<Shell />} />
      </Routes>
    </AuthProvider>
  )
}
