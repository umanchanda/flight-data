import { useEffect, useMemo, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";
import {
  Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { getAircraft, getAirports, getFlights, getRegistration } from "./api";

const navItems = [
  ["flights", "Flights", "✈"],
  ["aircraft", "Aircraft", "▱"],
  ["airports", "Airports", "⌖"],
  ["registrations", "Registrations", "№"],
];

const toHours = (flight) => (flight.duration_minutes || 0) / 60;
const dateValue = (flight) => flight.date ? new Date(`${flight.date}T00:00:00`) : null;
const formatDate = (value) => value ? new Intl.DateTimeFormat("en", { month: "short", day: "numeric", year: "numeric" }).format(new Date(`${value}T00:00:00`)) : "—";

function useData(loader, initial = []) {
  const [data, setData] = useState(initial);
  const [error, setError] = useState("");
  useEffect(() => { loader().then(setData).catch((reason) => setError(reason.message)); }, [loader]);
  return { data, error };
}

function App() {
  const [page, setPage] = useState("flights");
  const flightsState = useData(getFlights);
  const aircraftState = useData(getAircraft);
  const airportsState = useData(getAirports);
  const loading = !flightsState.data.length && !flightsState.error;
  const error = flightsState.error || aircraftState.error || airportsState.error;

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">✈</span><span>FLIGHT<br /><strong>DIARY</strong></span></div>
      <p className="eyebrow">Personal aviation log</p>
      <nav>{navItems.map(([id, label, icon]) => <button className={page === id ? "nav-item active" : "nav-item"} onClick={() => setPage(id)} key={id}><span>{icon}</span>{label}</button>)}</nav>
      <div className="sidebar-footer"><span className="status-dot" /> Live flight history</div>
    </aside>
    <main className="main-content">
      <header className="topbar"><span className="breadcrumb">FLIGHT DIARY <b>/</b> {page.toUpperCase()}</span><span className="date-stamp">Updated from your flight log</span></header>
      {error && <div className="error-banner">Could not reach the flight API. Check `FLIGHT_API_URL` and make sure FastAPI is running.</div>}
      {loading ? <Loading /> : <>
        {page === "flights" && <FlightsPage flights={flightsState.data} />}
        {page === "aircraft" && <AircraftPage flights={flightsState.data} aircraft={aircraftState.data} />}
        {page === "airports" && <AirportsPage flights={flightsState.data} airports={airportsState.data} />}
        {page === "registrations" && <RegistrationsPage flights={flightsState.data} />}
      </>}
    </main>
  </div>;
}

function Loading() { return <div className="loading"><span className="loader" />Loading your flight log...</div>; }

function PageIntro({ kicker, title, children }) { return <div className="page-intro"><div><p className="kicker">{kicker}</p><h1>{title}</h1></div>{children}</div>; }

function Metric({ label, value, detail }) { return <div className="metric"><span>{label}</span><strong>{value}</strong>{detail && <small>{detail}</small>}</div>; }

function FlightsPage({ flights }) {
  const [filters, setFilters] = useState({ years: [], airlines: [], aircraft: [], class: "", seatType: "", ticket: "", duration: null });
  const [pageNum, setPageNum] = useState(1);
  const updateFilters = (next) => { setFilters(next); setPageNum(1); };
  const years = [...new Set(flights.map((flight) => dateValue(flight)?.getFullYear()).filter(Boolean))].sort((a, b) => b - a);
  const airlines = [...new Set(flights.map((flight) => flight.airline).filter(Boolean))].sort();
  const aircraftTypes = [...new Set(flights.map((flight) => flight.aircraft).filter(Boolean))].sort();
  const classes = [...new Set(flights.map((flight) => flight.flight_class).filter(Boolean))].sort();
  const seatTypes = [...new Set(flights.map((flight) => flight.seat_type).filter(Boolean))].sort();
  const durationHours = flights.map(toHours);
  const minDuration = durationHours.length ? Math.floor(Math.min(...durationHours) * 2) / 2 : 0;
  const maxDuration = durationHours.length ? Math.ceil(Math.max(...durationHours) * 2) / 2 : 0;
  const filtered = flights.filter((flight) => {
    const yearMatch = !filters.years.length || filters.years.includes(dateValue(flight)?.getFullYear());
    const airlineMatch = !filters.airlines.length || filters.airlines.includes(flight.airline);
    const aircraftMatch = !filters.aircraft.length || filters.aircraft.includes(flight.aircraft);
    const classMatch = !filters.class || flight.flight_class === filters.class;
    const seatTypeMatch = !filters.seatType || flight.seat_type === filters.seatType;
    const durationMatch = !filters.duration || (toHours(flight) >= filters.duration[0] && toHours(flight) <= filters.duration[1]);
    const ticketMatch = !filters.ticket || (filters.ticket === "Nonrev" ? /nonrev/i.test(flight.note || "") : !/nonrev/i.test(flight.note || ""));
    return yearMatch && airlineMatch && aircraftMatch && classMatch && seatTypeMatch && durationMatch && ticketMatch;
  });
  const PAGE_SIZE = 50;
  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(pageNum, pageCount);
  const pageFlights = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);
  const yearsData = aggregate(filtered, (flight) => dateValue(flight)?.getFullYear(), "flights").sort((a, b) => Number(a.name) - Number(b.name));
  const airlineData = aggregate(filtered, (flight) => flight.airline, "flights").slice(0, 8);
  const routeData = aggregate(filtered, (flight) => `${flight.from_airport} → ${flight.to_airport}`, "flights").slice(0, 8);
  const hoursData = aggregate(filtered, (flight) => flight.airline, "hours", toHours);
  const topAircraftData = aggregate(filtered, (flight) => flight.aircraft, "flights").slice(0, 5);
  const topAirportData = aggregate(filtered.flatMap((flight) => [shortAirport(flight.from_airport), shortAirport(flight.to_airport)]), (airport) => airport, "flights").slice(0, 5);
  const topRouteData = aggregate(filtered, (flight) => `${shortAirport(flight.from_airport)} → ${shortAirport(flight.to_airport)}`, "flights").slice(0, 5);
  const totalHours = filtered.reduce((sum, flight) => sum + toHours(flight), 0);
  return <>
    <PageIntro kicker="Your flight log" title="Flights"><span className="record-count">{filtered.length} records</span></PageIntro>
    <section className="metrics"><Metric label="Total flights" value={filtered.length} /><Metric label="Hours flown" value={`${totalHours.toFixed(1)} h`} /><Metric label="Airlines" value={new Set(filtered.map((f) => f.airline)).size} /><Metric label="Airports visited" value={new Set(filtered.flatMap((f) => [f.from_airport, f.to_airport])).size} /></section>
    <section className="filter-panel"><div className="filter-heading"><span>Filter your log</span><button className="clear-button" onClick={() => updateFilters({ years: [], airlines: [], aircraft: [], class: "", seatType: "", ticket: "", duration: null })}>Clear filters</button></div><div className="filters">
      <MultiSelect label="Year" options={years} selected={filters.years} onChange={(years) => updateFilters({ ...filters, years })} />
      <MultiSelect label="Airline" options={airlines} selected={filters.airlines} onChange={(airlines) => updateFilters({ ...filters, airlines })} />
      <MultiSelect label="Aircraft type" options={aircraftTypes} selected={filters.aircraft} onChange={(aircraft) => updateFilters({ ...filters, aircraft })} />
      <RadioGroup label="Class" name="class-filter" value={filters.class} options={classes} onChange={(value) => updateFilters({ ...filters, class: value })} />
      <RadioGroup label="Seat type" name="seat-type-filter" value={filters.seatType} options={seatTypes} onChange={(value) => updateFilters({ ...filters, seatType: value })} />
      <RadioGroup label="Ticket type" name="ticket-filter" value={filters.ticket} options={["Revenue", "Nonrev"]} onChange={(value) => updateFilters({ ...filters, ticket: value })} />
      <DurationFilter min={minDuration} max={maxDuration} value={filters.duration} onChange={(duration) => updateFilters({ ...filters, duration })} />
    </div></section>
    <section className="section-block"><div className="section-title"><h2>Highlights</h2><span>Based on current filters</span></div><div className="split-grid three-col"><SimpleList title="Top 5 aircraft types" items={topAircraftData} /><SimpleList title="Top 5 airports" items={topAirportData} /><SimpleList title="Top 5 routes" items={topRouteData} /></div></section>
    <section className="section-block"><div className="section-title"><h2>Flight records</h2><span>Newest first</span></div><FlightTable flights={pageFlights} /><Pagination page={currentPage} pageCount={pageCount} onChange={setPageNum} /></section>
    <div className="chart-grid"><Chart title="Flights by airline" data={airlineData} /><Chart title="Flights per year" data={yearsData} /><Chart title="Top routes" data={routeData} /><Chart title="Hours by airline" data={hoursData} dataKey="hours" /></div>
    <RepeatAircraftSection flights={filtered} />
  </>;
}

function Pagination({ page, pageCount, onChange }) {
  if (pageCount <= 1) return null;
  return <div className="pagination">
    <button type="button" disabled={page <= 1} onClick={() => onChange(page - 1)}>← Previous</button>
    <span>Page {page} of {pageCount}</span>
    <button type="button" disabled={page >= pageCount} onClick={() => onChange(page + 1)}>Next →</button>
  </div>;
}

function RepeatAircraftSection({ flights }) {
  const repeats = aggregate(flights.filter((flight) => flight.registration), (flight) => flight.registration, "flights").filter((row) => row.flights > 1);
  if (!repeats.length) return null;
  return <section className="section-block">
    <div className="section-title"><h2>🔁 Repeat aircraft</h2><span>{repeats.length} registrations flown more than once</span></div>
    <div className="repeat-list">{repeats.map((row) => <details className="repeat-item" key={row.name}><summary><strong className="mono">{row.name}</strong><span className="tag">{row.flights} flights</span></summary><FlightTable flights={flights.filter((flight) => flight.registration === row.name).sort((a, b) => (b.date || "").localeCompare(a.date || ""))} /></details>)}</div>
  </section>;
}

function MultiSelect({ label, options, selected, onChange }) {
  const toggle = (option) => onChange(selected.includes(option) ? selected.filter((value) => value !== option) : [...selected, option]);
  return <details className="multiselect"><summary>{label}{selected.length > 0 && ` · ${selected.length}`}</summary><div className="multiselect-panel">{options.map((option) => <label key={option}><input type="checkbox" checked={selected.includes(option)} onChange={() => toggle(option)} />{option}</label>)}{options.length === 0 && <p className="muted">No options available.</p>}{selected.length > 0 && <button type="button" className="clear-button" onClick={() => onChange([])}>Clear</button>}</div></details>;
}

function RadioGroup({ label, name, value, options, onChange }) {
  return <div className="radio-group"><span className="radio-group-label">{label}</span><div className="radio-group-options">
    <label><input type="radio" name={name} checked={value === ""} onChange={() => onChange("")} />All</label>
    {options.map((option) => <label key={option}><input type="radio" name={name} checked={value === option} onChange={() => onChange(option)} />{option}</label>)}
  </div></div>;
}

function DurationFilter({ min, max, value, onChange }) {
  const [lo, hi] = value || [min, max];
  return <div className="duration-filter">
    <div className="radio-group-label">Duration (hours){value && <button type="button" className="clear-button" onClick={() => onChange(null)}>Reset</button>}</div>
    <label className="duration-row"><span>Min</span><input type="range" min={min} max={max} step={0.5} value={lo} onChange={(event) => onChange([Math.min(Number(event.target.value), hi), hi])} /><strong>{lo.toFixed(1)} h</strong></label>
    <label className="duration-row"><span>Max</span><input type="range" min={min} max={max} step={0.5} value={hi} onChange={(event) => onChange([lo, Math.max(Number(event.target.value), lo)])} /><strong>{hi.toFixed(1)} h</strong></label>
  </div>;
}

function aggregate(items, keyFn, valueKey, valueFn = () => 1) { const result = {}; items.forEach((item) => { const key = keyFn(item); if (key) result[key] = (result[key] || 0) + valueFn(item); }); return Object.entries(result).map(([name, value]) => ({ name, [valueKey]: Number(value.toFixed?.(1) || value) })).sort((a, b) => b[valueKey] - a[valueKey]); }
function Chart({ title, data, dataKey = "flights" }) { return <article className="chart-card"><div className="section-title"><h2>{title}</h2><span>{data.length} categories</span></div><ResponsiveContainer width="100%" height={220}><BarChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: -20 }}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#dbe5ec" /><XAxis dataKey="name" tick={{ fontSize: 10, fill: "#617283" }} tickLine={false} axisLine={false} /><YAxis allowDecimals={false} tick={{ fontSize: 10, fill: "#617283" }} tickLine={false} axisLine={false} /><Tooltip cursor={{ fill: "#edf4f7" }} /><Bar dataKey={dataKey} fill="#ef8354" radius={[3, 3, 0, 0]} /></BarChart></ResponsiveContainer></article>; }

function FlightTable({ flights }) { return <div className="table-wrap"><table><thead><tr><th>Date</th><th>Flight</th><th>Departure</th><th>Arrival</th><th>Dep</th><th>Arr</th><th>Airline</th><th>Aircraft</th><th>Reg</th><th>Duration</th><th>Class</th><th>Seat</th><th>Seat Type</th><th>Ticket</th></tr></thead><tbody>{flights.map((flight) => <tr key={flight.id}><td>{formatDate(flight.date)}</td><td className="mono">{flight.flight_number || "—"}</td><td><strong>{shortAirport(flight.from_airport)}</strong></td><td><strong>{shortAirport(flight.to_airport)}</strong></td><td className="mono">{formatTime(flight.dep_time)}</td><td className="mono">{formatTime(flight.arr_time)}</td><td>{flight.airline}</td><td>{flight.aircraft || "—"}</td><td className="mono">{flight.registration || "—"}</td><td>{toHours(flight).toFixed(1)} h</td><td><span className="tag">{flight.flight_class || "—"}</span></td><td className="mono">{flight.seat_number || "—"}</td><td>{flight.seat_type || "—"}</td><td><span className="tag">{isNonrev(flight) ? "Nonrev" : "Revenue"}</span></td></tr>)}</tbody></table>{!flights.length && <div className="empty">No flights match these filters.</div>}</div>; }
function shortAirport(value) { const match = String(value || "").match(/\(([A-Z]{3})\//); return match?.[1] || value || "—"; }
function formatTime(value) { return value ? String(value).slice(0, 5) : "—"; }
function isNonrev(flight) { return /nonrev/i.test(flight.note || ""); }

function AircraftPage({ flights, aircraft }) { const [selected, setSelected] = useState(aircraft[0]?.aircraft || ""); const current = aircraft.find((item) => item.aircraft === selected); const ownFlights = flights.filter((flight) => flight.aircraft === selected); const specs = current?.specifications; return <><PageIntro kicker="Your fleet" title="Aircraft"><select className="hero-select" value={selected} onChange={(event) => setSelected(event.target.value)}>{aircraft.map((item) => <option key={item.aircraft}>{item.aircraft}</option>)}</select></PageIntro>{current && <><p className="lead">{specs?.intro || "A closer look at the aircraft type in your personal flight history."}</p><div className="split-grid"><InfoTable title="Specifications" rows={specs ? { Manufacturer: specs.manufacturer, Family: specs.family, Type: specs.type, Engines: specs.engines, Range: `${specs.range_km?.toLocaleString()} km`, Capacity: `${specs.capacity} seats`, Wingspan: `${specs.wingspan_m} m`, Length: `${specs.length_m} m`, "Max speed": `${specs.max_speed_kmh} km/h`, "First flight": specs.first_flight } : null} /><article className="panel"><h2>Your stats on this type</h2><div className="mini-metrics"><Metric label="Flights" value={ownFlights.length} /><Metric label="Hours flown" value={`${ownFlights.reduce((sum, flight) => sum + toHours(flight), 0).toFixed(1)} h`} /><Metric label="Airlines" value={new Set(ownFlights.map((flight) => flight.airline)).size} /></div></article></div><div className="split-grid"><SimpleList title="Airlines flown with" items={aggregate(ownFlights, (flight) => flight.airline, "flights")} /><SimpleList title="Routes flown" items={aggregate(ownFlights, (flight) => `${shortAirport(flight.from_airport)} → ${shortAirport(flight.to_airport)}`, "flights")} /></div></>}</>; }
function InfoTable({ title, rows }) { return <article className="panel"><h2>{title}</h2>{rows ? <dl>{Object.entries(rows).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value || "—"}</dd></div>)}</dl> : <p className="muted">No specification data available for this aircraft.</p>}</article>; }
function SimpleList({ title, items }) { return <article className="panel"><h2>{title}</h2><div className="simple-list">{items.map((item) => <div key={item.name}><span>{item.name}</span><strong>{item.flights}</strong></div>)}{!items.length && <p className="muted">No recorded flights.</p>}</div></article>; }

function AirportsPage({ flights, airports }) { const [selected, setSelected] = useState(airports[0]?.code || ""); const current = airports.find((airport) => airport.code === selected); const arrivals = flights.filter((flight) => shortAirport(flight.to_airport) === selected); const departures = flights.filter((flight) => shortAirport(flight.from_airport) === selected); const visits = [...arrivals, ...departures]; const sortedVisits = [...visits].sort((a, b) => (a.date || "").localeCompare(b.date || "")); return <><PageIntro kicker="Places you have touched" title="Airports"><span className="record-count">{airports.length} airports</span></PageIntro><MapContainer className="flight-map" center={[22, 8]} zoom={2} scrollWheelZoom={false}><TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />{airports.filter((airport) => airport.lat && airport.lon).map((airport) => <CircleMarker center={[airport.lat, airport.lon]} radius={Math.min(13, 5 + airport.total_visits / 3)} pathOptions={{ color: airport.code === selected ? "#ef8354" : "#1f7a8c", fillColor: airport.code === selected ? "#ef8354" : "#1f7a8c", fillOpacity: .8 }} eventHandlers={{ click: () => setSelected(airport.code) }} key={airport.code}><Popup><strong>{airport.code}</strong><br />{airport.name}<br />{airport.total_visits} visits</Popup></CircleMarker>)}</MapContainer><div className="airport-toolbar"><label>Explore an airport<select value={selected} onChange={(event) => setSelected(event.target.value)}>{airports.map((airport) => <option key={airport.code} value={airport.code}>{airport.name} ({airport.code})</option>)}</select></label></div>{current && <><div className="split-grid"><InfoTable title="Airport info" rows={{ Name: current.name, City: current.city, "State / Region": current.state_region, Country: current.country, IATA: current.code, ICAO: current.icao, Elevation: current.elevation ? `${Math.round(current.elevation)} ft` : "—", Timezone: current.timezone }} /><article className="panel"><h2>Your stats</h2><div className="mini-metrics"><Metric label="Total visits" value={visits.length} /><Metric label="Departures" value={departures.length} /><Metric label="Arrivals" value={arrivals.length} /><Metric label="First visit" value={formatDate(sortedVisits[0]?.date)} /><Metric label="Last visit" value={formatDate(sortedVisits[sortedVisits.length - 1]?.date)} /></div></article></div><div className="split-grid"><SimpleList title="Destinations from here" items={aggregate(departures, (flight) => shortAirport(flight.to_airport), "flights")} /><SimpleList title="Origins into here" items={aggregate(arrivals, (flight) => shortAirport(flight.from_airport), "flights")} /></div></>}</>; }

function RegistrationsPage({ flights }) { const registrations = [...new Set(flights.map((flight) => flight.registration).filter(Boolean))].sort(); const [selected, setSelected] = useState(registrations[0] || ""); const [detail, setDetail] = useState(null); useEffect(() => { if (selected) getRegistration(selected).then(setDetail).catch(() => setDetail(null)); }, [selected]); const ownFlights = flights.filter((flight) => flight.registration === selected); const meta = detail?.meta; return <><PageIntro kicker="Aircraft by registration" title="Registrations"><select className="hero-select" value={selected} onChange={(event) => setSelected(event.target.value)}>{registrations.map((registration) => <option key={registration}>{registration}</option>)}</select></PageIntro><div className="split-grid registration-head"><InfoTable title={selected} rows={meta ? { Operator: meta.operator, Manufacturer: meta.manufacturer, Model: meta.model, "ICAO type": meta.icao_type, Country: meta.country, "Mode-S (hex)": meta.mode_s } : null} />{meta?.photo_url && <figure className="photo-panel"><img src={meta.photo_url} alt={`Aircraft ${selected}`} /><figcaption>© Planespotters.net{meta.operator ? ` · ${meta.operator}` : ""}</figcaption></figure>}</div><section className="metrics"><Metric label="Flights on this aircraft" value={ownFlights.length} /><Metric label="Hours flown" value={`${ownFlights.reduce((sum, flight) => sum + toHours(flight), 0).toFixed(1)} h`} /><Metric label="First flight" value={formatDate(ownFlights.reduce((first, flight) => !first || flight.date < first ? flight.date : first, ""))} /><Metric label="Last flight" value={formatDate(ownFlights.reduce((last, flight) => !last || flight.date > last ? flight.date : last, ""))} /></section><section className="section-block"><div className="section-title"><h2>Flight history on this aircraft</h2></div><FlightTable flights={ownFlights} /></section></>; }

export default App;