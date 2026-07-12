from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.dependencies import get_db
from app.models.catalog import Emirate, City, Category
from app.schemas.catalog import Emirate as EmirateSchema, City as CitySchema, Category as CategorySchema

router = APIRouter()

@router.get("/emirates", response_model=List[EmirateSchema])
def list_emirates(include_hidden: bool = False, db: Session = Depends(get_db)):
    query = db.query(Emirate)
    if not include_hidden:
        query = query.filter(Emirate.is_visible == True)
    return query.all()

@router.get("/cities", response_model=List[CitySchema])
def list_cities(emirate_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(City)
    if emirate_id:
        query = query.filter(City.emirate_id == emirate_id)
    return query.all()

@router.get("/services", response_model=List[CategorySchema])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()
