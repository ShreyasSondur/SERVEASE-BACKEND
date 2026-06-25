from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_active_partner, get_current_user_optional
from app.models.user import User, UserRole
from app.models.partner import PartnerProfile, PartnerStatus
from app.models.business import Deal, Service
from app.schemas.business import Deal as DealSchema, DealCreate, DealUpdate

router = APIRouter()

@router.get("/", response_model=List[DealSchema])
def list_deals(
    skip: int = 0, 
    limit: int = 100,
    emirate_id: int | None = None,
    city_id: int | None = None,
    category_id: int | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    # Join with PartnerProfile to ensure only verified partners' deals are shown
    query = db.query(Deal).join(PartnerProfile).filter(
        Deal.is_active == True,
        Deal.is_deleted == False,
        PartnerProfile.status == PartnerStatus.VERIFIED
    )

    if city_id:
        query = query.filter(Deal.city_id == city_id)
    if emirate_id:
        from app.models.catalog import City
        query = query.join(City, Deal.city_id == City.id).filter(City.emirate_id == emirate_id)
    if category_id:
        query = query.filter(Deal.category_id == category_id)
    if q:
        query = query.filter(Deal.title.ilike(f"%{q}%"))

    # Log the search in search history
    from app.models.analytics import SearchHistory
    search_log = SearchHistory(
        user_id=current_user.id if current_user else None,
        emirate_id=emirate_id,
        city_id=city_id,
        category_id=category_id,
        search_query=q
    )
    db.add(search_log)
    db.commit()

    deals = query.offset(skip).limit(limit).all()
    results = [DealSchema.model_validate(d) for d in deals]
    if not current_user:
        for d in results:
            if d.partner:
                d.partner.phone = "HIDDEN_LOGIN_REQUIRED"
                d.partner.email = "HIDDEN_LOGIN_REQUIRED"
    return results

@router.post("/", response_model=DealSchema)
def create_deal(
    deal_in: DealCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_partner),
):
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first()
    if not profile or profile.status != PartnerStatus.VERIFIED:
        raise HTTPException(status_code=403, detail="Only verified partners can create deals.")
    
    current_deals_count = db.query(Deal).filter(Deal.partner_id == profile.id, Deal.is_deleted == False).count()
    if current_deals_count >= profile.deals_limit:
        raise HTTPException(status_code=400, detail=f"Deal limit of {profile.deals_limit} reached.")
        
    deal = Deal(
        partner_id=profile.id,
        category_id=deal_in.category_id,
        city_id=deal_in.city_id,
        title=deal_in.title,
        description=deal_in.description,
        images=deal_in.images,
        discount_desc=deal_in.discount_desc,
        expiry_date=deal_in.expiry_date,
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return deal

@router.put("/{deal_id}", response_model=DealSchema)
def update_deal(
    deal_id: int,
    deal_in: DealUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_partner),
):
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first()
    deal = db.query(Deal).filter(Deal.id == deal_id, Deal.is_deleted == False).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found.")
    if deal.partner_id != profile.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough privileges to update this deal.")
    if profile.status in [PartnerStatus.SUSPENDED, PartnerStatus.BANNED]:
        raise HTTPException(status_code=403, detail="Suspended or banned partners cannot modify deals.")
        
    update_data = deal_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(deal, field, value)
        
    db.commit()
    db.refresh(deal)
    return deal

@router.delete("/{deal_id}", response_model=dict)
def delete_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_partner),
):
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first()
    deal = db.query(Deal).filter(Deal.id == deal_id, Deal.is_deleted == False).first()
    
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found.")
    if deal.partner_id != profile.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough privileges to delete this deal.")
    if profile.status in [PartnerStatus.SUSPENDED, PartnerStatus.BANNED]:
        raise HTTPException(status_code=403, detail="Suspended or banned partners cannot modify deals.")
        
    deal.is_deleted = True
    db.commit()
    return {"detail": "Deal deleted successfully."}

@router.get("/{deal_id}", response_model=DealSchema)
def get_deal(
    deal_id: int, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    deal = db.query(Deal).filter(Deal.id == deal_id, Deal.is_deleted == False).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found.")
        
    result = DealSchema.model_validate(deal)
    if not current_user:
        if result.partner:
            result.partner.phone = "HIDDEN_LOGIN_REQUIRED"
            result.partner.email = "HIDDEN_LOGIN_REQUIRED"
    return result
