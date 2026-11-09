from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# البيانات اللي المستخدم هيبعتها وهو بيسجل
class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone_number: Optional[str] = None
    license_plate: Optional[str] = None
    car_model: Optional[str] = None

# شكل البيانات اللي هترجع في الرد (بدون الباسوورد طبعاً للأمان)
class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    license_plate: Optional[str] = None
    car_model: Optional[str] = None
    role: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True