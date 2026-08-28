from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    space_id = Column(Integer, ForeignKey("parking_spaces.id"), nullable=False)

    # Driver information (no auth needed for prototype)
    driver_name = Column(String, nullable=False)
    vehicle_plate = Column(String, nullable=False)  # e.g. "ASW 1234"

    # Possible values: "active", "completed", "cancelled"
    status = Column(String, default="active", nullable=False)

    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)  # Can be set later

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    space = relationship("ParkingSpace", back_populates="reservations")