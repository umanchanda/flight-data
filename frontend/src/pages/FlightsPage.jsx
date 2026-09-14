import { useEffect, useMemo, useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { apiFetch } from '../api'
import DataTable from '../components/DataTable'
import MetricGrid from '../components/MetricGrid'
import { ErrorState, LoadingState } from '../components/StatusView'
import { formatDate, formatDurationMinutes, formatHours, formatTime } from '../utils'

function buildDefaultFilters(filterOptions) {
  return {
    year: [],
    airline: [],
    from_airport: [],
    to_airport: [],
    flight_class: [],
    aircraft: [],
    seat_type: [],
    flight_reason: [],
    ticket_type: 'all',
    date_from: filterOptions.date_min ?? '',
    date_to: filterOptions.date_max ?? '',
  }
}

function dashboardParams(filters) {
  return {
    year: filters.year,
    airline: filters.airline,
    from_airport: filters.from_airport,
    to_airport: filters.to_airport,
    flight_class: filters.flight_class,
    aircraft: filters.aircraft,
    seat_type: filters.seat_type,
    flight_reason: filters.flight_reason,
    ticket_type: filters.ticket_type === 'all' ? undefined : filters.ticket_type,
    date_from: filters.date_from,
    date_to: filters.date_to,
  }
}

function MultiSelect({ label, name, value, options, onChange }) {
  return (
    <label className="field-group">
      <span>{label}</span>
      <select
        multiple
        name={name}
        value={value}
        onChange={(event) =>
          onChange(
            name,
            Array.from(event.target.selectedOptions, (option) => option.value),
          )
        }
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  )
}

function ChartCard({ title, data, dataKey, labelKey = 'label' }) {
  return (
    <section className="card">
      <div className="card-heading">
        <h2>{title}</h2>
      </div>
      {data.length ? (
        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 12, right: 12, left: 0, bottom: 40 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey={labelKey} angle={-25} textAnchor="end" interval={0} height={70} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey={dataKey} fill="#2563eb" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="status-card">No chart data for this filter set.</div>
      )}
    </section>
  )
}

export default function FlightsPage() {
  const [dashboard, setDashboard] = useState(null)
  const [filters, setFilters] = useState(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const controller = new AbortController()

    async function load() {
      try {
        setLoading(true)
        const result = await apiFetch('/dashboard', {}, controller.signal)
        setDashboard(result)
        setFilters(buildDefaultFilters(result.filters))
      } catch (loadError) {
        if (loadError.name !== 'AbortError') {
          setError(loadError.message)
        }
      } finally {
        setLoading(false)
      }
    }

    load()
    return () => controller.abort()
  }, [])

  const flightColumns = useMemo(
    () => [
      { key: 'date', label: 'Date', render: (row) => formatDate(row.date) },
      { key: 'flight_number', label: 'Flight #', render: (row) => row.flight_number || '—' },
      { key: 'from_airport', label: 'From' },
      { key: 'to_airport', label: 'To' },
      { key: 'dep_time', label: 'Dep', render: (row) => formatTime(row.dep_time) },
      { key: 'arr_time', label: 'Arr', render: (row) => formatTime(row.arr_time) },
      {
        key: 'duration_minutes',
        label: 'Duration (h)',
        render: (row) => formatDurationMinutes(row.duration_minutes),
      },
      { key: 'airline', label: 'Airline' },
      { key: 'aircraft', label: 'Aircraft', render: (row) => row.aircraft || '—' },
      { key: 'registration', label: 'Reg', render: (row) => row.registration || '—' },
      { key: 'seat_number', label: 'Seat', render: (row) => row.seat_number || '—' },
      { key: 'seat_type', label: 'Seat type', render: (row) => row.seat_type || '—' },
      { key: 'flight_class', label: 'Class', render: (row) => row.flight_class || '—' },
      { key: 'flight_reason', label: 'Reason', render: (row) => row.flight_reason || '—' },
      { key: 'note', label: 'Note', render: (row) => row.note || '—' },
    ],
    [],
  )

  async function runDashboard(nextFilters) {
    try {
      setSubmitting(true)
      setError('')
      const result = await apiFetch('/dashboard', dashboardParams(nextFilters))
      setDashboard(result)
    } catch (loadError) {
      setError(loadError.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading || !filters) {
    return <LoadingState message="Loading flights dashboard…" />
  }

  if (error && !dashboard) {
    return <ErrorState message={error} />
  }

  return (
    <div className="page-grid page-grid-wide">
      <aside className="card filter-card">
        <div className="card-heading">
          <h2>Filters</h2>
        </div>
        <div className="filter-grid">
          <MultiSelect
            label="Year"
            name="year"
            value={filters.year.map(String)}
            options={dashboard.filters.years.map(String)}
            onChange={(name, value) => setFilters((current) => ({ ...current, [name]: value.map(Number) }))}
          />
          <MultiSelect
            label="Airline"
            name="airline"
            value={filters.airline}
            options={dashboard.filters.airlines}
            onChange={(name, value) => setFilters((current) => ({ ...current, [name]: value }))}
          />
          <MultiSelect
            label="From airport"
            name="from_airport"
            value={filters.from_airport}
            options={dashboard.filters.airports}
            onChange={(name, value) => setFilters((current) => ({ ...current, [name]: value }))}
          />
          <MultiSelect
            label="To airport"
            name="to_airport"
            value={filters.to_airport}
            options={dashboard.filters.airports}
            onChange={(name, value) => setFilters((current) => ({ ...current, [name]: value }))}
          />
          <MultiSelect
            label="Class"
            name="flight_class"
            value={filters.flight_class}
            options={dashboard.filters.classes}
            onChange={(name, value) => setFilters((current) => ({ ...current, [name]: value }))}
          />
          <MultiSelect
            label="Aircraft"
            name="aircraft"
            value={filters.aircraft}
            options={dashboard.filters.aircraft}
            onChange={(name, value) => setFilters((current) => ({ ...current, [name]: value }))}
          />
          <MultiSelect
            label="Seat type"
            name="seat_type"
            value={filters.seat_type}
            options={dashboard.filters.seat_types}
            onChange={(name, value) => setFilters((current) => ({ ...current, [name]: value }))}
          />
          <MultiSelect
            label="Flight reason"
            name="flight_reason"
            value={filters.flight_reason}
            options={dashboard.filters.reasons}
            onChange={(name, value) => setFilters((current) => ({ ...current, [name]: value }))}
          />
          <label className="field-group">
            <span>Ticket type</span>
            <select
              value={filters.ticket_type}
              onChange={(event) =>
                setFilters((current) => ({ ...current, ticket_type: event.target.value }))
              }
            >
              <option value="all">All</option>
              <option value="revenue">Revenue</option>
              <option value="nonrev">Nonrev</option>
            </select>
          </label>
          <label className="field-group">
            <span>Date from</span>
            <input
              type="date"
              value={filters.date_from}
              min={dashboard.filters.date_min ?? undefined}
              max={filters.date_to || dashboard.filters.date_max || undefined}
              onChange={(event) =>
                setFilters((current) => ({ ...current, date_from: event.target.value }))
              }
            />
          </label>
          <label className="field-group">
            <span>Date to</span>
            <input
              type="date"
              value={filters.date_to}
              min={filters.date_from || dashboard.filters.date_min || undefined}
              max={dashboard.filters.date_max ?? undefined}
              onChange={(event) =>
                setFilters((current) => ({ ...current, date_to: event.target.value }))
              }
            />
          </label>
        </div>
        <div className="button-row">
          <button type="button" onClick={() => runDashboard(filters)} disabled={submitting}>
            {submitting ? 'Applying…' : 'Apply filters'}
          </button>
          <button
            type="button"
            className="button-secondary"
            onClick={() => {
              const reset = buildDefaultFilters(dashboard.filters)
              setFilters(reset)
              runDashboard(reset)
            }}
            disabled={submitting}
          >
            Reset
          </button>
        </div>
      </aside>

      <div className="page-stack">
        {error ? <ErrorState message={error} /> : null}
        <MetricGrid
          items={[
            { label: 'Total flights', value: dashboard.summary.total_flights },
            { label: 'Total hours flown', value: formatHours(dashboard.summary.total_hours) },
            { label: 'Airlines', value: dashboard.summary.unique_airlines },
            { label: 'Airports visited', value: dashboard.summary.unique_airports },
          ]}
        />

        <section className="card">
          <div className="card-heading">
            <h2>Flights ({dashboard.flights.length})</h2>
          </div>
          <DataTable columns={flightColumns} rows={dashboard.flights} emptyMessage="No flights match these filters." />
        </section>

        <div className="chart-grid">
          <ChartCard title="Flights by airline" data={dashboard.charts.flights_by_airline} dataKey="value" />
          <ChartCard title="Flights per year" data={dashboard.charts.flights_per_year} dataKey="value" />
          <ChartCard title="Top routes" data={dashboard.charts.top_routes} dataKey="count" labelKey="route" />
          <ChartCard title="Hours by airline" data={dashboard.charts.hours_by_airline} dataKey="value" />
        </div>

        <section className="card">
          <div className="card-heading">
            <h2>Repeat aircraft</h2>
            <p>Registrations you have flown on more than once.</p>
          </div>
          {dashboard.repeat_aircraft.length ? (
            <div className="accordion-list">
              {dashboard.repeat_aircraft.map((item) => (
                <details key={item.registration}>
                  <summary>
                    <span>{item.registration}</span>
                    <strong>{item.flights} flights</strong>
                  </summary>
                  <DataTable
                    columns={[
                      { key: 'date', label: 'Date', render: (row) => formatDate(row.date) },
                      { key: 'flight_number', label: 'Flight #', render: (row) => row.flight_number || '—' },
                      { key: 'from_airport', label: 'From' },
                      { key: 'to_airport', label: 'To' },
                      { key: 'airline', label: 'Airline' },
                      { key: 'aircraft', label: 'Aircraft', render: (row) => row.aircraft || '—' },
                    ]}
                    rows={item.history}
                  />
                </details>
              ))}
            </div>
          ) : (
            <div className="status-card">No repeat registrations for this filter set.</div>
          )}
        </section>
      </div>
    </div>
  )
}
