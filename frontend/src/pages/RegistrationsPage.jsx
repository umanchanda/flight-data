import { useEffect, useMemo, useState } from 'react'

import { apiFetch } from '../api'
import DataTable from '../components/DataTable'
import MetricGrid from '../components/MetricGrid'
import { ErrorState, LoadingState } from '../components/StatusView'
import { formatDate, formatDurationMinutes, formatHours } from '../utils'

export default function RegistrationsPage() {
  const [registrations, setRegistrations] = useState([])
  const [selected, setSelected] = useState('')
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const controller = new AbortController()

    async function loadRegistrations() {
      try {
        setLoading(true)
        const result = await apiFetch('/registrations', {}, controller.signal)
        setRegistrations(result)
        if (result.length) {
          setSelected(result[0].registration)
        }
      } catch (loadError) {
        if (loadError.name !== 'AbortError') {
          setError(loadError.message)
        }
      } finally {
        setLoading(false)
      }
    }

    loadRegistrations()
    return () => controller.abort()
  }, [])

  useEffect(() => {
    if (!selected) return undefined
    const controller = new AbortController()

    async function loadDetail() {
      try {
        setLoading(true)
        setError('')
        const result = await apiFetch(`/registrations/${selected}`, {}, controller.signal)
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

  const selectedRegistration = useMemo(
    () => registrations.find((item) => item.registration === selected),
    [registrations, selected],
  )

  if (loading && !detail) {
    return <LoadingState message="Loading registration details…" />
  }

  if (error && !detail) {
    return <ErrorState message={error} />
  }

  return (
    <div className="page-stack">
      {error ? <ErrorState message={error} /> : null}
      <section className="card">
        <div className="card-heading">
          <h2>Registrations</h2>
        </div>
        <label className="field-group field-inline">
          <span>Select a registration</span>
          <select value={selected} onChange={(event) => setSelected(event.target.value)}>
            {registrations.map((item) => (
              <option key={item.registration} value={item.registration}>
                {item.registration} {item.aircraft ? `— ${item.aircraft}` : ''}
              </option>
            ))}
          </select>
        </label>
      </section>

      {detail ? (
        <>
          <div className="two-column-grid two-column-grid-wide-right">
            <section className="card">
              <div className="card-heading">
                <h2>{selected}</h2>
                {selectedRegistration?.aircraft ? <p>{selectedRegistration.aircraft}</p> : null}
              </div>
              {detail.meta ? (
                <dl className="definition-list">
                  <div>
                    <dt>Operator</dt>
                    <dd>{detail.meta.operator || '—'}</dd>
                  </div>
                  <div>
                    <dt>Manufacturer</dt>
                    <dd>{detail.meta.manufacturer || '—'}</dd>
                  </div>
                  <div>
                    <dt>Model</dt>
                    <dd>{detail.meta.model || '—'}</dd>
                  </div>
                  <div>
                    <dt>ICAO type</dt>
                    <dd>{detail.meta.icao_type || '—'}</dd>
                  </div>
                  <div>
                    <dt>Country</dt>
                    <dd>{detail.meta.country || '—'}</dd>
                  </div>
                  <div>
                    <dt>Mode-S (hex)</dt>
                    <dd>{detail.meta.mode_s || '—'}</dd>
                  </div>
                </dl>
              ) : (
                <div className="status-card">No external data found for this registration.</div>
              )}
            </section>

            <section className="card">
              <div className="card-heading">
                <h2>Photo</h2>
              </div>
              {detail.meta?.photo ? (
                <figure className="photo-card">
                  <img src={detail.meta.photo.url} alt={`Aircraft ${selected}`} />
                  <figcaption>
                    {detail.meta.photo.photographer
                      ? `© ${detail.meta.photo.photographer} via Planespotters.net`
                      : '© Planespotters.net'}
                    {detail.meta.photo.link ? (
                      <>
                        {' '}
                        <a href={detail.meta.photo.link} target="_blank" rel="noreferrer">
                          View source
                        </a>
                      </>
                    ) : null}
                  </figcaption>
                </figure>
              ) : (
                <div className="status-card">No photo available for this registration.</div>
              )}
            </section>
          </div>

          <section className="card">
            <div className="card-heading">
              <h2>Your stats on this aircraft</h2>
            </div>
            <MetricGrid
              items={[
                { label: 'Flights on this aircraft', value: detail.stats.total_flights },
                { label: 'Hours flown', value: formatHours(detail.stats.total_hours) },
                { label: 'First flight', value: formatDate(detail.stats.first_flight) },
                { label: 'Last flight', value: formatDate(detail.stats.last_flight) },
              ]}
            />
          </section>

          <section className="card">
            <div className="card-heading">
              <h2>Flight history on this aircraft</h2>
            </div>
            <DataTable
              columns={[
                { key: 'date', label: 'Date', render: (row) => formatDate(row.date) },
                { key: 'flight_number', label: 'Flight #', render: (row) => row.flight_number || '—' },
                { key: 'from_airport', label: 'From' },
                { key: 'to_airport', label: 'To' },
                { key: 'airline', label: 'Airline' },
                { key: 'aircraft', label: 'Aircraft type', render: (row) => row.aircraft || '—' },
                {
                  key: 'duration_minutes',
                  label: 'Duration (h)',
                  render: (row) => formatDurationMinutes(row.duration_minutes),
                },
              ]}
              rows={detail.flights}
            />
          </section>
        </>
      ) : null}
    </div>
  )
}
