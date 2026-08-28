from fastapi import APIRouter

from app.api.v1 import occupancy
from app.api.v1 import zones
from app.api.v1 import availability
from app.api.v1 import reservations

# The main v1 router — included by main.py
v1_router = APIRouter(prefix="/api/v1")

# Register all endpoint groups
v1_router.include_router(occupancy.router, tags=["Occupancy"])
v1_router.include_router(zones.router, tags=["Zones"])
v1_router.include_router(availability.router, tags=["Availability"])
v1_router.include_router(reservations.router, tags=["Reservations"])