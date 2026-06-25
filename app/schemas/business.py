from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .catalog import City, Category
from .partner import PartnerProfile

class ServiceBase(BaseModel):
    category_id: int
    city_id: int
    title: str
    description: str
    images: List[str] = []
    emergency_service: Optional[str] = "Available 24/7"
    provider_type: Optional[str] = "Licensed Company"
    is_active: Optional[bool] = True

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    category_id: Optional[int] = None
    city_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    images: Optional[List[str]] = None
    emergency_service: Optional[str] = None
    provider_type: Optional[str] = None
    is_active: Optional[bool] = None

class Service(ServiceBase):
    id: int
    partner_id: int
    created_at: datetime
    city: Optional[City] = None
    category: Optional[Category] = None
    partner: Optional[PartnerProfile] = None

    class Config:
        from_attributes = True


class DealBase(BaseModel):
    category_id: int
    city_id: int
    title: str
    description: str
    images: List[str] = []
    discount_desc: str
    expiry_date: datetime
    is_active: Optional[bool] = True

class DealCreate(DealBase):
    pass

class DealUpdate(BaseModel):
    category_id: Optional[int] = None
    city_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    images: Optional[List[str]] = None
    discount_desc: Optional[str] = None
    expiry_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class Deal(DealBase):
    id: int
    partner_id: int
    created_at: datetime
    city: Optional[City] = None
    category: Optional[Category] = None
    partner: Optional[PartnerProfile] = None

    class Config:
        from_attributes = True
