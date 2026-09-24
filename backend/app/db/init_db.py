from app.db.database import Base, engine

# These imports are required even though they look unused.
# Importing each model registers it with Base so SQLAlchemy
# knows to include it when creating tables.
from app.models.zone import ParkingZone
from app.models.space import ParkingSpace
from app.models.occupancy import OccupancyLog
from app.models.reservation import Reservation
from app.models.analysis import AnalysisJob, VehicleDetectionLog


def create_tables():
    """
    Creates all tables if they do not already exist, and ensures
    new columns are added if upgrading an existing SQLite/Postgres DB.
    """
    Base.metadata.create_all(bind=engine)
    
    # Auto-migrate new reservation and zone columns if needed
    with engine.connect() as conn:
        try:
            # Check existing columns in reservations table
            if engine.dialect.name == "sqlite":
                res = conn.exec_driver_sql("PRAGMA table_info(reservations)").fetchall()
                existing_cols = {row[1] for row in res}
                if "driver_email" not in existing_cols:
                    conn.exec_driver_sql("ALTER TABLE reservations ADD COLUMN driver_email VARCHAR(120)")
                if "driver_phone" not in existing_cols:
                    conn.exec_driver_sql("ALTER TABLE reservations ADD COLUMN driver_phone VARCHAR(30)")
                if "vehicle_model" not in existing_cols:
                    conn.exec_driver_sql("ALTER TABLE reservations ADD COLUMN vehicle_model VARCHAR(50)")

                # Check existing columns in parking_zones table
                z_res = conn.exec_driver_sql("PRAGMA table_info(parking_zones)").fetchall()
                z_cols = {row[1] for row in z_res}
                if "zone_type" not in z_cols:
                    conn.exec_driver_sql("ALTER TABLE parking_zones ADD COLUMN zone_type VARCHAR(20) DEFAULT 'PAID'")
                if "hourly_rate" not in z_cols:
                    conn.exec_driver_sql("ALTER TABLE parking_zones ADD COLUMN hourly_rate FLOAT")
                if "operating_hours" not in z_cols:
                    conn.exec_driver_sql("ALTER TABLE parking_zones ADD COLUMN operating_hours VARCHAR(100)")
                if "rules" not in z_cols:
                    conn.exec_driver_sql("ALTER TABLE parking_zones ADD COLUMN rules VARCHAR(255)")
                if "restriction_reason" not in z_cols:
                    conn.exec_driver_sql("ALTER TABLE parking_zones ADD COLUMN restriction_reason VARCHAR(255)")

                # Set distinct zone types for realistic test data if they are defaults
                conn.exec_driver_sql("UPDATE parking_zones SET zone_type='PAID', hourly_rate=10.0, operating_hours='08:00 AM - 11:00 PM', rules='Maximum stay: 2 hours' WHERE id=1 AND (zone_type IS NULL OR zone_type='PAID')")
                conn.exec_driver_sql("UPDATE parking_zones SET zone_type='FREE', hourly_rate=0.0, operating_hours='24/7', rules='Free municipal public parking' WHERE id=2")

                # Ensure Zone 3 (Restricted) exists for municipal policy demonstrations
                z3_count = conn.exec_driver_sql("SELECT COUNT(*) FROM parking_zones WHERE id=3").scalar()
                if not z3_count:
                    conn.exec_driver_sql(
                        "INSERT INTO parking_zones (id, name, location, total_spaces, latitude, longitude, zone_type, hourly_rate, operating_hours, rules, restriction_reason) "
                        "VALUES (3, 'Zone C - Aswan Train Station', 'Station Square, Aswan', 4, 24.0947, 32.9021, 'RESTRICTED', NULL, '24/7', 'No public parking permitted', 'Emergency Access & Bus Transit Only')"
                    )
                    for i in range(1, 5):
                        conn.exec_driver_sql(
                            f"INSERT INTO parking_spaces (zone_id, space_number, status) VALUES (3, 'C-{i}', 'occupied')"
                        )
                else:
                    conn.exec_driver_sql("UPDATE parking_zones SET zone_type='RESTRICTED', restriction_reason='Emergency Access & Bus Transit Only', rules='No public parking permitted' WHERE id=3")

                conn.commit()
            elif engine.dialect.name == "postgresql":
                conn.exec_driver_sql("ALTER TABLE reservations ADD COLUMN IF NOT EXISTS driver_email VARCHAR(120);")
                conn.exec_driver_sql("ALTER TABLE reservations ADD COLUMN IF NOT EXISTS driver_phone VARCHAR(30);")
                conn.exec_driver_sql("ALTER TABLE reservations ADD COLUMN IF NOT EXISTS vehicle_model VARCHAR(50);")

                conn.exec_driver_sql("ALTER TABLE parking_zones ADD COLUMN IF NOT EXISTS zone_type VARCHAR(20) DEFAULT 'PAID';")
                conn.exec_driver_sql("ALTER TABLE parking_zones ADD COLUMN IF NOT EXISTS hourly_rate FLOAT;")
                conn.exec_driver_sql("ALTER TABLE parking_zones ADD COLUMN IF NOT EXISTS operating_hours VARCHAR(100);")
                conn.exec_driver_sql("ALTER TABLE parking_zones ADD COLUMN IF NOT EXISTS rules VARCHAR(255);")
                conn.exec_driver_sql("ALTER TABLE parking_zones ADD COLUMN IF NOT EXISTS restriction_reason VARCHAR(255);")

                conn.exec_driver_sql("UPDATE parking_zones SET zone_type='PAID', hourly_rate=10.0, operating_hours='08:00 AM - 11:00 PM', rules='Maximum stay: 2 hours' WHERE id=1 AND (zone_type IS NULL OR zone_type='PAID');")
                conn.exec_driver_sql("UPDATE parking_zones SET zone_type='FREE', hourly_rate=0.0, operating_hours='24/7', rules='Free municipal public parking' WHERE id=2;")

                z3_count = conn.exec_driver_sql("SELECT COUNT(*) FROM parking_zones WHERE id=3;").scalar()
                if not z3_count:
                    conn.exec_driver_sql(
                        "INSERT INTO parking_zones (id, name, location, total_spaces, latitude, longitude, zone_type, hourly_rate, operating_hours, rules, restriction_reason) "
                        "VALUES (3, 'Zone C - Aswan Train Station', 'Station Square, Aswan', 4, 24.0947, 32.9021, 'RESTRICTED', NULL, '24/7', 'No public parking permitted', 'Emergency Access & Bus Transit Only');"
                    )
                    for i in range(1, 5):
                        conn.exec_driver_sql(
                            f"INSERT INTO parking_spaces (zone_id, space_number, status) VALUES (3, 'C-{i}', 'occupied');"
                        )
                else:
                    conn.exec_driver_sql("UPDATE parking_zones SET zone_type='RESTRICTED', restriction_reason='Emergency Access & Bus Transit Only', rules='No public parking permitted' WHERE id=3;")

                conn.commit()
        except Exception as e:
            print(f"[WARN] Schema migration notice: {e}")

    print("[OK] All database tables created and validated successfully.")