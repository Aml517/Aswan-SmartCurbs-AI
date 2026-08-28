from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class ParkingZone(Base):
    __tablename__ = "parking_zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)           # e.g. "Zone A - Corniche"
    location = Column(String, nullable=False)        # e.g. "Corniche Street, Aswan"
    total_spaces = Column(Integer, nullable=False)   # Total number of spaces in this zone
    latitude = Column(Float, nullable=True)          # GPS coordinates (optional for demo)
    longitude = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # One zone has many spaces
    spaces = relationship("ParkingSpace", back_populates="zone")