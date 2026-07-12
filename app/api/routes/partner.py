from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.api.dependencies import get_db, get_current_user, get_current_active_partner
from app.models.user import User, UserRole
from app.models.partner import PartnerProfile, PartnerStatus
from app.models.business import Service, Deal
from app.schemas.partner import PartnerProfileCreate, PartnerProfileUpdate, PartnerProfile as PartnerProfileSchema
from app.schemas.business import Service as ServiceSchema, ServiceCreate, Deal as DealSchema, DealCreate

router = APIRouter()

@router.post("/apply", response_model=PartnerProfileSchema)
def apply_for_partner(
    profile_in: PartnerProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.USER:
        raise HTTPException(status_code=400, detail="Only standard users can apply to be a partner.")
    
    existing_profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first()
    if existing_profile:
        raise HTTPException(status_code=400, detail="You have already applied for a partner profile.")
    
    new_profile = PartnerProfile(
        user_id=current_user.id,
        first_name=profile_in.first_name,
        last_name=profile_in.last_name,
        phone=profile_in.phone,
        emirate=profile_in.emirate,
        city=profile_in.city,
        emirate_id_number=profile_in.emirate_id_number,
        business_name=profile_in.business_name,
        emirates_id_url=profile_in.emirates_id_url,
        status=PartnerStatus.PENDING
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return new_profile

@router.get("/profile", response_model=PartnerProfileSchema)
def get_partner_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Partner profile not found.")
    return profile

@router.put("/profile", response_model=PartnerProfileSchema)
def update_partner_profile(
    profile_in: PartnerProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Partner profile not found.")
    
    if profile_in.business_name:
        profile.business_name = profile_in.business_name
    if profile_in.emirates_id_url:
        profile.emirates_id_url = profile_in.emirates_id_url
        
    db.commit()
    db.refresh(profile)
    return profile

# -----------------
# Services (Partner Only)
# -----------------
@router.get("/services", response_model=List[ServiceSchema])
def get_partner_services(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_partner),
):
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Partner profile not found.")
    
    services = db.query(Service).options(
        joinedload(Service.city),
        joinedload(Service.category),
        joinedload(Service.partner)
    ).filter(Service.partner_id == profile.id, Service.is_deleted == False).all()
    return services

@router.post("/services", response_model=ServiceSchema)
def create_partner_service(
    service_in: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_partner),
):
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Partner profile not found.")
    if profile.status != PartnerStatus.VERIFIED:
        raise HTTPException(status_code=403, detail="Only verified partners can create services.")
        
    current_services_count = db.query(Service).filter(
        Service.partner_id == profile.id, 
        Service.is_deleted == False
    ).count()
    if current_services_count >= profile.services_limit:
        raise HTTPException(status_code=400, detail=f"Service limit of {profile.services_limit} reached.")
        
    service = Service(
        partner_id=profile.id,
        category_id=service_in.category_id,
        city_id=service_in.city_id,
        title=service_in.title,
        description=service_in.description,
        images=service_in.images,
        emergency_service=service_in.emergency_service,
        provider_type=service_in.provider_type,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service

@router.delete("/services/{service_id}", response_model=dict)
def delete_partner_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_partner),
):
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Partner profile not found.")
    if profile.status in [PartnerStatus.SUSPENDED, PartnerStatus.BANNED]:
        raise HTTPException(status_code=403, detail="Suspended or banned partners cannot modify services.")
        
    service = db.query(Service).filter(
        Service.id == service_id, 
        Service.partner_id == profile.id, 
        Service.is_deleted == False
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found.")
        
    service.is_deleted = True
    db.commit()
    return {"detail": "Service deleted successfully."}

# -----------------
# Deals (Partner Only)
# -----------------
@router.get("/deals", response_model=List[DealSchema])
def get_partner_deals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_partner),
):
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Partner profile not found.")
    
    deals = db.query(Deal).options(
        joinedload(Deal.city),
        joinedload(Deal.category),
        joinedload(Deal.partner)
    ).filter(Deal.partner_id == profile.id, Deal.is_deleted == False).all()
    return deals

@router.post("/deals", response_model=DealSchema)
def create_partner_deal(
    deal_in: DealCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_partner),
):
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Partner profile not found.")
    if profile.status != PartnerStatus.VERIFIED:
        raise HTTPException(status_code=403, detail="Only verified partners can create deals.")
        
    current_deals_count = db.query(Deal).filter(
        Deal.partner_id == profile.id, 
        Deal.is_deleted == False
    ).count()
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

@router.delete("/deals/{deal_id}", response_model=dict)
def delete_partner_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_partner),
):
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Partner profile not found.")
    if profile.status in [PartnerStatus.SUSPENDED, PartnerStatus.BANNED]:
        raise HTTPException(status_code=403, detail="Suspended or banned partners cannot modify deals.")
        
    deal = db.query(Deal).filter(
        Deal.id == deal_id, 
        Deal.partner_id == profile.id, 
        Deal.is_deleted == False
    ).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found.")
        
    deal.is_deleted = True
    db.commit()
    return {"detail": "Deal deleted successfully."}
