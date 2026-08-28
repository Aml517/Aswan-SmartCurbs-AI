from app.db.database import Base, engine

# These imports are required even though they look unused.
# Importing each model registers it with Base so SQLAlchemy
# knows to include it when creating tables.
from app.models.zone import ParkingZone
from app.models.space import ParkingSpace
from app.models.occupancy import OccupancyLog
from app.models.reservation import Reservation


def create_tables():
    """
    Creates all tables in PostgreSQL if they do not already exist.
    Safe to call on every startup — it will not drop existing data.
    """
    Base.metadata.create_all(bind=engine)
    print("✅ All database tables created successfully.")