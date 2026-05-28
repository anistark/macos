import { BrowserRouter, Route, Routes } from 'react-router-dom'
import RunsList from './pages/RunsList'
import RunDetail from './pages/RunDetail'
import TrajectoryView from './pages/TrajectoryView'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RunsList />} />
        <Route path="/r/:runId" element={<RunDetail />} />
        <Route path="/r/:runId/t/:taskId" element={<TrajectoryView />} />
      </Routes>
    </BrowserRouter>
  )
}
