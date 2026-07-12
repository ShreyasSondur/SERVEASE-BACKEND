from pydantic import BaseModel
from typing import Optional, List

# Emirate Schemas
class EmirateBase(BaseModel):
    name: str

class EmirateCreate(EmirateBase):
    pass

class Emirate(EmirateBase):
    id: int
    is_visible: bool = True

    class Config:
        from_attributes = True

# City Schemas
class CityBase(BaseModel):
    name: str
    emirate_id: int

class CityCreate(CityBase):
    pass

class City(CityBase):
    id: int
    emirate: Optional[Emirate] = None

    class Config:
        from_attributes = True

# Category Schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True
