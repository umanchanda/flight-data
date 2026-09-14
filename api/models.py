from datetime import date, time
from typing import Optional

from pydantic import BaseModel


class Flight(BaseModel):
    id: int
    date: Optional[date]
    flight_number: Optional[str]
    from_airport: str
    to_airport: str
    dep_time: Optional[time]
    arr_time: Optional[time]
    duration_minutes: Optional[int]
    airline: str
    aircraft: Optional[str]
    registration: Optional[str]
    seat_number: Optional[str]
    seat_type: Optional[str]
    flight_class: Optional[str]
    flight_reason: Optional[str]
    note: Optional[str]


class Stats(BaseModel):
    total_flights: int
    total_hours: float
    unique_airlines: int
    unique_airports: int


class AircraftSummary(BaseModel):
    aircraft: str
    flights: int
    total_hours: float
    airlines: list[str]


class AircraftSpec(BaseModel):
    manufacturer: str
    family: str
    type: str
    engines: str
    range_km: int
    capacity: str
    wingspan_m: float
    length_m: float
    max_speed_kmh: int
    first_flight: str
    intro: str


class AircraftStats(BaseModel):
    flights: int
    total_hours: float
    unique_airlines: int


class AirlineFlights(BaseModel):
    airline: str
    flights: int


class RouteFlights(BaseModel):
    route: str
    flights: int


class AircraftDetail(BaseModel):
    name: str
    available_aircraft: list[str]
    spec: Optional[AircraftSpec]
    stats: AircraftStats
    airlines: list[AirlineFlights]
    routes: list[RouteFlights]


class AirportSummary(BaseModel):
    code: str
    name: str
    city: str
    country: str
    departures: int
    arrivals: int
    total_visits: int
    lat: Optional[float]
    lon: Optional[float]


class AirportInfo(BaseModel):
    name: str
    city: str
    state_region: str
    country: str
    iata: str
    icao: str
    elevation_ft: Optional[float]
    timezone: str
    lat: Optional[float]
    lon: Optional[float]


class AirportStatsDetail(BaseModel):
    total_visits: int
    departures: int
    arrivals: int
    first_visit: Optional[date]
    last_visit: Optional[date]


class AirportRouteCount(BaseModel):
    airport: str
    label: str
    flights: int


class AirportDetail(BaseModel):
    info: AirportInfo
    stats: AirportStatsDetail
    destinations: list[AirportRouteCount]
    origins: list[AirportRouteCount]
    airlines: list[AirlineFlights]


class RegistrationListItem(BaseModel):
    registration: str
    flights: int
    aircraft: Optional[str]


class RegistrationPhoto(BaseModel):
    url: str
    photographer: Optional[str]
    link: Optional[str]


class RegistrationMeta(BaseModel):
    registration: str
    manufacturer: Optional[str]
    model: Optional[str]
    icao_type: Optional[str]
    operator: Optional[str]
    country: Optional[str]
    mode_s: Optional[str]
    photo: Optional[RegistrationPhoto]


class RegistrationStats(BaseModel):
    total_flights: int
    total_hours: float
    first_flight: Optional[date]
    last_flight: Optional[date]


class RegistrationDetail(BaseModel):
    meta: Optional[RegistrationMeta]
    stats: RegistrationStats
    flights: list[Flight]


class CountPoint(BaseModel):
    label: str
    value: int


class FloatPoint(BaseModel):
    label: str
    value: float


class RouteCount(BaseModel):
    route: str
    count: int


class RepeatFlight(BaseModel):
    date: Optional[date]
    flight_number: Optional[str]
    from_airport: str
    to_airport: str
    airline: str
    aircraft: Optional[str]


class RepeatAircraft(BaseModel):
    registration: str
    flights: int
    history: list[RepeatFlight]


class DashboardFilters(BaseModel):
    years: list[int]
    airlines: list[str]
    airports: list[str]
    classes: list[str]
    aircraft: list[str]
    seat_types: list[str]
    reasons: list[str]
    date_min: Optional[date]
    date_max: Optional[date]


class DashboardCharts(BaseModel):
    flights_by_airline: list[CountPoint]
    flights_per_year: list[CountPoint]
    top_routes: list[RouteCount]
    hours_by_airline: list[FloatPoint]


class DashboardData(BaseModel):
    summary: Stats
    filters: DashboardFilters
    flights: list[Flight]
    charts: DashboardCharts
    repeat_aircraft: list[RepeatAircraft]
