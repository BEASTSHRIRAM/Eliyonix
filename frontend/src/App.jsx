import { BrowserRouter, Routes, Route } from 'react-router-dom'
import LandingPage from './pages/LandingPage'
import AgentMonitor from './pages/AgentMonitor'
import RecommendationsPage from './pages/RecommendationsPage'
import FarmerDashboard from './pages/FarmerDashboard'
import EnterpriseDashboard from './pages/EnterpriseDashboard'
import './index.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/dashboard" element={<EnterpriseDashboard />} />
        <Route path="/enterprise-dashboard" element={<EnterpriseDashboard />} />
        <Route path="/agents" element={<AgentMonitor />} />
        <Route path="/recommendations" element={<RecommendationsPage />} />
        <Route path="/farmer-dashboard" element={<FarmerDashboard />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
