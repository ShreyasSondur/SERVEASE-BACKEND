from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.user import UserRole

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

class UserInDBBase(UserBase):
    id: int
    role: UserRole
    is_banned: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass
