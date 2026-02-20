import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { Sessions } from './pages/Sessions'
import { SessionDetail } from './pages/SessionDetail'
import { Agents } from './pages/Agents'
import { Memory } from './pages/Memory'
import { Orchestration } from './pages/Orchestration'
import { Interventions } from './pages/Interventions'
import { Settings } from './pages/Settings'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/sessions" element={<Sessions />} />
        <Route path="/sessions/:id" element={<SessionDetail />} />
        <Route path="/agents" element={<Agents />} />
        <Route path="/memory" element={<Memory />} />
        <Route path="/orchestration" element={<Orchestration />} />
        <Route path="/interventions" element={<Interventions />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  )
}

export default App
