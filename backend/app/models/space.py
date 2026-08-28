from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class ParkingSpace(Base):
    __tablename__ = "parking_spaces"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("parking_zones.id"), nullable=False)
    space_number = Column(String, nullable=False)    # e.g. "A1", "A2", "B3"

    # The AI module updates this field via POST /api/v1/occupancy
    # Possible values: "available", "occupied", "reserved"
    status = Column(String, default="available", nullable=False)

    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    zone = relationship("ParkingZone", back_populates="spaces")
    occupancy_logs = relationship("OccupancyLog", back_populates="space")
    reservations = relationship("Reservation", back_populates="space")