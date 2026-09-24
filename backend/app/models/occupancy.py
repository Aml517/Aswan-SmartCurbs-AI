from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class OccupancyLog(Base):
    __tablename__ = "occupancy_logs"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("parking_zones.id"), nullable=False)
    space_id = Column(Integer, ForeignKey("parking_spaces.id"), nullable=False)

    # Status sent by the AI: "occupied" or "available"
    status = Column(String, nullable=False)

    # How confident the AI model was (0.0 to 1.0)
    confidence = Column(Float, nullable=True)

    # Where this update came from — useful for debugging
    source = Column(String, default="ai_module")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    space = relationship("ParkingSpace", back_populates="occupancy_logs")