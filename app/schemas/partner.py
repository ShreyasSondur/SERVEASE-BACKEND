from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime
from app.models.partner import PartnerStatus

class PartnerProfileBase(BaseModel):
    first_name: str
    last_name: str
    phone: str
    emirate: str
    city: str
    emirate_id_number: str
    business_name: Optional[str] = None
    emirates_id_url: str

class PartnerProfileCreate(PartnerProfileBase):
    pass

class PartnerProfileUpdate(BaseModel):
    business_name: Optional[str] = None
    emirates_id_url: Optional[str] = None

class PartnerProfileInDBBase(PartnerProfileBase):
    id: int
    user_id: int
    is_verified: bool
    status: PartnerStatus
    services_limit: int
    deals_limit: int
    suspended_until: Optional[datetime] = None
    created_at: datetime
    email: Optional[str] = None

    class Config:
        from_attributes = True

class PartnerProfile(PartnerProfileInDBBase):
    pass
