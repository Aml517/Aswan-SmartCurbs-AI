from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserResponse
from app.services.security import hash_password

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    # 1. التحقق إن الإيميل مش موجود قبل كده
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="البريد الإلكتروني مسجل بالفعل!"
        )

    # 2. تشفير كلمة المرور
    hashed_pwd = hash_password(user_data.password)

    # 3. إنشاء كائن المستخدم وحفظه
    new_user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        phone_number=user_data.phone_number,
        hashed_password=hashed_pwd,
        license_plate=user_data.license_plate,
        car_model=user_data.car_model,
        role="driver"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user