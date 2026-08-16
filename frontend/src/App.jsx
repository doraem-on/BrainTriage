import { Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import NewPatient from './pages/NewPatient'
import PatientDetail from './pages/PatientDetail'

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark" />
          BrainTriage
        </div>
        <nav className="nav-links">
          <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>Dashboard</NavLink>
          <NavLink to="/new" className={({ isActive }) => isActive ? 'active' : ''}>New Patient</NavLink>
        </nav>
        <div className="sidebar-footer">
          Precision Care Challenge 2026<br />
          AI-driven prioritization for early Alzheimer's diagnostic pathways.<br /><br />
          Synthetic data demo — see Model Card.
        </div>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/new" element={<NewPatient />} />
          <Route path="/patients/:id" element={<PatientDetail />} />
        </Routes>
      </main>
    </div>
  )
}
