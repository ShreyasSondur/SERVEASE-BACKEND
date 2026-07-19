from pydantic import BaseModel
from typing import Optional

class AdConfigBase(BaseModel):
    position: str
    image_url: Optional[str] = None
    redirect_url: Optional[str] = None
    is_active: bool = False

class AdConfigUpdate(BaseModel):
    image_url: Optional[str] = None
    redirect_url: Optional[str] = None
    is_active: Optional[bool] = None

class AdConfigResponse(AdConfigBase):
    id: int

    class Config:
        from_attributes = True
