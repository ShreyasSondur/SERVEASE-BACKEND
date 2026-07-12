from pydantic import BaseModel, EmailStr, Field

class ContactForm(BaseModel):
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    email: EmailStr
    message: str = Field(..., max_length=500)
