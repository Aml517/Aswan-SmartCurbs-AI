from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    
    # بيانات خاصة بالسائق لمشروع SmartCurbs
    license_plate = Column(String, nullable=True)  # رقم اللوحة
    car_model = Column(String, nullable=True)      # نوع السيارة
    role = Column(String, default="driver", nullable=False)  # driver / admin

    created_at = Column(DateTime(timezone=True), server_default=func.now())