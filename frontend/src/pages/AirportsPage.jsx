import { useEffect, useMemo, useState } from 'react'
import { ComposableMap, Geographies, Geography, Marker } from 'react-simple-maps'

import { apiFetch } from '../api'
import DataTable from '../components/DataTable'
import MetricGrid from '../components/MetricGrid'
import { ErrorState, LoadingState } from '../components/StatusView'
import { formatDate } from '../utils'

const geoUrl = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json'

export default function AirportsPage() {
  const [airports, setAirports] = useState([])
  const [selectedCode, setSelectedCode] = useState('')
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const controller = new AbortController()

    async function loadAirports() {
      try {
        setLoading(true)
        const result = await apiFetch('/airports', {}, controller.signal)
        setAirports(result)
        if (result.length) {
          setSelectedCode(result[0].code)
        }
      } catch (loadError) {
        if (loadError.name !== 'AbortError') {
          setError(loadError.message)
        }
      } finally {
        setLoading(false)
      }
    }

    loadAirports()
    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (!selectedCode) return undefined
    const controller = new AbortController()

    async function loadDetail() {
      try {
        setLoading(true)
        setError('')
        const result = await apiFetch(`/airports/${selectedCode}`, {}, controller.signal)
        setDetail(result)
      } catch (loadError) {
        if (loadError.name !== 'AbortError') {
          setError(loadError.message)
        }
      } finally {
        setLoading(false)
      }
    }

    loadDetail()
    return () => controller.abort()
  }, [selectedCode])

  const selectedAirport = useMemo(
    () => airports.find((item) => item.code === selectedCode),
    [airports, selectedCode],
  )

  if (loading && !detail) {
    return <LoadingState message="Loading airport data…" />
  }

  if (error && !detail) {
    return <ErrorState message={error} />
  }

  return (
    <div className="page-stack">
      {error ? <ErrorState message={error} /> : null}
      <section className="card">
        <div className="card-heading">
          <h2>Airports visited: {airports.length}</h2>
        </div>
        <div className="map-wrap">
          <ComposableMap projectionConfig={{ scale: 150 }}>
            <Geographies geography={geoUrl}>
              {({ geographies }) =>
                geographies.map((geography) => (
                  <Geography
                    key={geography.rsmKey}
                    geography={geography}
                    fill="#e2e8f0"
                    stroke="#94a3b8"
                    strokeWidth={0.3}
                  />
                ))
              }
            </Geographies>
            {airports
              .filter((item) => item.lat != null && item.lon != null)
              .map((item) => (
                <Marker key={item.code} coordinates={[item.lon, item.lat]}>
                  <circle
                    r={item.code === selectedCode ? 6 : 4}
                    fill={item.code === selectedCode ? '#0f172a' : '#2563eb'}
                    stroke="#ffffff"
                    strokeWidth={1.5}
                    onClick={() => setSelectedCode(item.code)}
                    style={{ cursor: 'pointer' }}
                  />
                </Marker>
              ))}
          </ComposableMap>
        </div>
      </section>

      <section className="card">
        <div className="card-heading">
          <h2>Airport detail</h2>
        </div>
        <label className="field-group field-inline">
          <span>Select an airport</span>
          <select value={selectedCode} onChange={(event) => setSelectedCode(event.target.value)}>
            {airports.map((item) => (
              <option key={item.code} value={item.code}>
                {item.name} ({item.code})
              </option>
            ))}
          </select>
        </label>
      </section>

      {detail ? (
        <>
          <div className="two-column-grid">
            <section className="card">
              <div className="card-heading">
                <h2>Airport info</h2>
              </div>
              <dl className="definition-list">
                <div>
                  <dt>Name</dt>
                  <dd>{detail.info.name}</dd>
                </div>
                <div>
                  <dt>City</dt>
                  <dd>{detail.info.city || '—'}</dd>
                </div>
                <div>
                  <dt>State / Region</dt>
                  <dd>{detail.info.state_region || '—'}</dd>
                </div>
                <div>
                  <dt>Country</dt>
                  <dd>{detail.info.country || '—'}</dd>
                </div>
                <div>
                  <dt>IATA</dt>
                  <dd>{detail.info.iata}</dd>
                </div>
                <div>
                  <dt>ICAO</dt>
                  <dd>{detail.info.icao || '—'}</dd>
                </div>
                <div>
                  <dt>Elevation</dt>
                  <dd>{detail.info.elevation_ft != null ? `${detail.info.elevation_ft} ft` : '—'}</dd>
                </div>
                <div>
                  <dt>Timezone</dt>
                  <dd>{detail.info.timezone || '—'}</dd>
                </div>
              </dl>
            </section>

            <section className="card">
              <div className="card-heading">
                <h2>Your stats</h2>
                {selectedAirport ? <p>{selectedAirport.name} ({selectedAirport.code})</p> : null}
              </div>
              <MetricGrid
                items={[
                  { label: 'Total visits', value: detail.stats.total_visits },
                  { label: 'Departures', value: detail.stats.departures },
                  { label: 'Arrivals', value: detail.stats.arrivals },
                  { label: 'First visit', value: formatDate(detail.stats.first_visit) },
                  { label: 'Last visit', value: formatDate(detail.stats.last_visit) },
                ]}
              />
            </section>
          </div>

          <div className="two-column-grid">
            <section className="card">
              <div className="card-heading">
                <h2>Destinations from here</h2>
              </div>
              <DataTable
                columns={[
                  { key: 'label', label: 'Destination' },
                  { key: 'flights', label: 'Flights' },
                ]}
                rows={detail.destinations}
                emptyMessage="No departures recorded."
              />
            </section>

            <section className="card">
              <div className="card-heading">
                <h2>Origins into here</h2>
              </div>
              <DataTable
                columns={[
                  { key: 'label', label: 'Origin' },
                  { key: 'flights', label: 'Flights' },
                ]}
                rows={detail.origins}
                emptyMessage="No arrivals recorded."
              />
            </section>
          </div>

          <section className="card">
            <div className="card-heading">
              <h2>Airlines used here</h2>
            </div>
            <DataTable
              columns={[
                { key: 'airline', label: 'Airline' },
                { key: 'flights', label: 'Flights' },
              ]}
              rows={detail.airlines}
            />
          </section>
        </>
      ) : null}
    </div>
  )
}
