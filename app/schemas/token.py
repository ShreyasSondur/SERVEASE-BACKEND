from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    requires_otp: Optional[bool] = False
    temp_token: Optional[str] = None

class TokenPayload(BaseModel):
    sub: Optional[str] = None

class VerifyOTP(BaseModel):
    temp_token: str
    otp: str

class ResendOTP(BaseModel):
    temp_token: str

