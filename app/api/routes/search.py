from typing import List, Optional
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user_optional
from app.models.user import User
from app.models.business import Service
from app.models.partner import PartnerProfile, PartnerStatus
from app.schemas.business import Service as ServiceSchema
from app.models.analytics import SearchHistory
from datetime import datetime, timezone

router = APIRouter()

@router.get("/", response_model=List[ServiceSchema])
def search_services(
    request: Request,
    emirate_id: Optional[int] = None,
    city_id: Optional[int] = None,
    category_id: Optional[int] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    query = db.query(Service).join(PartnerProfile).filter(
        Service.is_active == True, 
        Service.is_deleted == False,
        PartnerProfile.status == PartnerStatus.VERIFIED
    )
    
    if city_id:
        query = query.filter(Service.city_id == city_id)
    if category_id:
        query = query.filter(Service.category_id == category_id)
    if q:
        query = query.filter(Service.title.ilike(f"%{q}%"))

    # Log the search with the authenticated user ID if available
    search_log = SearchHistory(
        user_id=current_user.id if current_user else None,
        emirate_id=emirate_id,
        city_id=city_id,
        category_id=category_id,
        search_query=q
    )
    db.add(search_log)
    db.commit()
        
    services = query.all()
    results = [ServiceSchema.model_validate(s) for s in services]
    if not current_user:
        for s in results:
            if s.partner:
                s.partner.phone = "HIDDEN_LOGIN_REQUIRED"
                s.partner.email = "HIDDEN_LOGIN_REQUIRED"
    return results
