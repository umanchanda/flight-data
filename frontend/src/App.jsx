import { Suspense, lazy } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import Layout from './components/Layout'
import { LoadingState } from './components/StatusView'

const FlightsPage = lazy(() => import('./pages/FlightsPage'))
const AircraftPage = lazy(() => import('./pages/AircraftPage'))
const AirportsPage = lazy(() => import('./pages/AirportsPage'))
const RegistrationsPage = lazy(() => import('./pages/RegistrationsPage'))

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Suspense fallback={<LoadingState message="Loading page…" />}>
          <Routes>
            <Route path="/" element={<FlightsPage />} />
            <Route path="/aircraft" element={<AircraftPage />} />
            <Route path="/airports" element={<AirportsPage />} />
            <Route path="/registrations" element={<RegistrationsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </Layout>
    </BrowserRouter>
  )
}
