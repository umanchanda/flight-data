from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import aircraft, airports, flights, registrations, stats

load_dotenv()

app = FastAPI(
    title="Flight Diary API",
    description="Personal flight history from Flightradar24.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(flights.router)
app.include_router(stats.router)
app.include_router(aircraft.router)
app.include_router(airports.router)
app.include_router(registrations.router)
