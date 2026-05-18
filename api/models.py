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


class AirportSummary(BaseModel):
    code: str
    name: str
    city: str
    country: str
    departures: int
    arrivals: int
    total_visits: int


class RegistrationMeta(BaseModel):
    registration: str
    manufacturer: Optional[str]
    model: Optional[str]
    icao_type: Optional[str]
    operator: Optional[str]
    country: Optional[str]
    mode_s: Optional[str]
    photo_url: Optional[str]
    photo_thumbnail_url: Optional[str]


class RegistrationDetail(BaseModel):
    meta: Optional[RegistrationMeta]
    flights: list[Flight]
