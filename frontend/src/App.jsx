import { Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import NewPatient from './pages/NewPatient'
import PatientDetail from './pages/PatientDetail'
import ResourceOptimizer from './pages/ResourceOptimizer'
import NeuralBrainCanvas from './components/NeuralBrainCanvas'

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark" />
          BrainTriage
        </div>
        <div className="brand-sidebar-viz">
          <NeuralBrainCanvas height={140} nodeColor={0x9085e9} edgeColor={0x4a3aa7} />
        </div>
        <nav className="nav-links">
          <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>
            <span className="nav-icon">◆</span> Dashboard
          </NavLink>
          <NavLink to="/new" className={({ isActive }) => isActive ? 'active' : ''}>
            <span className="nav-icon">＋</span> New Patient
          </NavLink>
          <NavLink to="/optimize" className={({ isActive }) => isActive ? 'active' : ''}>
            <span className="nav-icon">⚙</span> Resource Optimizer
          </NavLink>
        </nav>
        <div className="sidebar-footer">
          <strong>Precision Care Challenge 2026</strong><br />
          Adaptive AI triage for early Alzheimer's diagnostic pathways.<br /><br />
          3 of 4 stages train on real published data — see Model Card.
        </div>
      </aside>
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/new" element={<NewPatient />} />
          <Route path="/optimize" element={<ResourceOptimizer />} />
          <Route path="/patients/:id" element={<PatientDetail />} />
        </Routes>
      </main>
    </div>
  )
}
