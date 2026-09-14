import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import aircraft, airports, dashboard, flights, registrations, stats

load_dotenv()

app = FastAPI(
    title='Flight Diary API',
    description='Personal flight history from Flightradar24.',
    version='2.0.0',
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        'FRONTEND_ORIGIN',
        'http://localhost:5173,http://127.0.0.1:5173',
    ).split(',')
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=['GET'],
    allow_headers=['*'],
)

app.include_router(dashboard.router)
app.include_router(flights.router)
app.include_router(stats.router)
app.include_router(aircraft.router)
app.include_router(airports.router)
app.include_router(registrations.router)
