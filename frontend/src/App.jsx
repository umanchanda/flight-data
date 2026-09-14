import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import Layout from './components/Layout'
import AircraftPage from './pages/AircraftPage'
import AirportsPage from './pages/AirportsPage'
import FlightsPage from './pages/FlightsPage'
import RegistrationsPage from './pages/RegistrationsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<FlightsPage />} />
          <Route path="/aircraft" element={<AircraftPage />} />
          <Route path="/airports" element={<AirportsPage />} />
          <Route path="/registrations" element={<RegistrationsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
