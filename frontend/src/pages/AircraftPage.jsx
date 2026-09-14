import { useEffect, useState } from 'react'

import { apiFetch } from '../api'
import DataTable from '../components/DataTable'
import MetricGrid from '../components/MetricGrid'
import { ErrorState, LoadingState } from '../components/StatusView'
import { formatHours } from '../utils'

const specLabels = [
  ['manufacturer', 'Manufacturer'],
  ['family', 'Family'],
  ['type', 'Type'],
  ['engines', 'Engines'],
  ['range_km', 'Range (km)'],
  ['capacity', 'Capacity'],
  ['wingspan_m', 'Wingspan (m)'],
  ['length_m', 'Length (m)'],
  ['max_speed_kmh', 'Max speed (km/h)'],
  ['first_flight', 'First flight'],
]

export default function AircraftPage() {
  const [aircraft, setAircraft] = useState([])
  const [selected, setSelected] = useState('')
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const controller = new AbortController()

    async function loadAircraft() {
      try {
        setLoading(true)
        const result = await apiFetch('/aircraft', {}, controller.signal)
        setAircraft(result)
        if (result.length) {
          setSelected(result[0].aircraft)
        }
      } catch (loadError) {
        if (loadError.name !== 'AbortError') {
          setError(loadError.message)
        }
      } finally {
        setLoading(false)
      }
    }

    loadAircraft()
    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (!selected) return undefined
    const controller = new AbortController()

    async function loadDetail() {
      try {
        setLoading(true)
        setError('')
        const result = await apiFetch(`/aircraft/${encodeURIComponent(selected)}`, {}, controller.signal)
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
  }, [selected])

  if (loading && !detail) {
    return <LoadingState message="Loading aircraft details…" />
  }

  if (error && !detail) {
    return <ErrorState message={error} />
  }

  return (
    <div className="page-stack">
      {error ? <ErrorState message={error} /> : null}
      <section className="card">
        <div className="card-heading">
          <h2>Aircraft</h2>
        </div>
        <label className="field-group field-inline">
          <span>Select an aircraft</span>
          <select value={selected} onChange={(event) => setSelected(event.target.value)}>
            {aircraft.map((item) => (
              <option key={item.aircraft} value={item.aircraft}>
                {item.aircraft}
              </option>
            ))}
          </select>
        </label>
      </section>

      {detail ? (
        <>
          <section className="card">
            <div className="card-heading">
              <h2>{detail.name}</h2>
              {detail.spec?.intro ? <p>{detail.spec.intro}</p> : null}
            </div>
          </section>

          <div className="two-column-grid">
            <section className="card">
              <div className="card-heading">
                <h2>Specifications</h2>
              </div>
              {detail.spec ? (
                <dl className="definition-list">
                  {specLabels.map(([key, label]) => (
                    <div key={key}>
                      <dt>{label}</dt>
                      <dd>{detail.spec[key]}</dd>
                    </div>
                  ))}
                </dl>
              ) : (
                <div className="status-card">No spec data available for this aircraft.</div>
              )}
            </section>

            <section className="card">
              <div className="card-heading">
                <h2>Your stats on this type</h2>
              </div>
              <MetricGrid
                items={[
                  { label: 'Flights', value: detail.stats.flights },
                  { label: 'Hours flown', value: formatHours(detail.stats.total_hours) },
                  { label: 'Airlines flown with', value: detail.stats.unique_airlines },
                ]}
              />
            </section>
          </div>

          <div className="two-column-grid">
            <section className="card">
              <div className="card-heading">
                <h2>Airlines flown with</h2>
              </div>
              <DataTable
                columns={[
                  { key: 'airline', label: 'Airline' },
                  { key: 'flights', label: 'Flights' },
                ]}
                rows={detail.airlines}
              />
            </section>

            <section className="card">
              <div className="card-heading">
                <h2>Routes flown</h2>
              </div>
              <DataTable
                columns={[
                  { key: 'route', label: 'Route' },
                  { key: 'flights', label: 'Flights' },
                ]}
                rows={detail.routes}
              />
            </section>
          </div>
        </>
      ) : null}
    </div>
  )
}
