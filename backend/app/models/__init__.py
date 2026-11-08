from app.models.zone import ParkingZone
from app.models.space import ParkingSpace
from app.models.occupancy import OccupancyLog
from app.models.reservation import Reservation
from app.models.analysis import AnalysisJob, VehicleDetectionLog
from app.models.test_session import AITestSession, DistanceMeasurementRecord

__all__ = [
    "ParkingZone",
    "ParkingSpace",
    "OccupancyLog",
    "Reservation",
    "AnalysisJob",
    "VehicleDetectionLog",
    "AITestSession",
    "DistanceMeasurementRecord",
]

