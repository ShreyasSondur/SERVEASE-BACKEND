from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.api.dependencies import get_db, get_current_active_partner, get_current_user_optional
from app.models.user import User, UserRole
from app.models.partner import PartnerProfile, PartnerStatus
from app.models.business import Service
from app.schemas.business import Service as ServiceSchema, ServiceCreate, ServiceUpdate

router = APIRouter()

@router.get("/", response_model=List[ServiceSchema])
def list_services(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    # Join with PartnerProfile to ensure only verified partners' services are shown
    services = db.query(Service).options(
        joinedload(Service.city),
        joinedload(Service.category),
        joinedload(Service.partner)
    ).join(PartnerProfile).filter(
        Service.is_active == True,
        Service.is_deleted == False,
        PartnerProfile.status == PartnerStatus.VERIFIED
    ).offset(skip).limit(limit).all()
    
    results = [ServiceSchema.model_validate(s) for s in services]
    if not current_user:
        for s in results:
            if s.partner:
                s.partner.phone = "HIDDEN_LOGIN_REQUIRED"
                s.partner.email = "HIDDEN_LOGIN_REQUIRED"
    return results

@router.post("/", response_model=ServiceSchema)
def create_service(
    service_in: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_partner),
):
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first()
    if not profile or profile.status != PartnerStatus.VERIFIED:
        raise HTTPException(status_code=403, detail="Only verified partners can create services.")
    
    current_services_count = db.query(Service).filter(Service.partner_id == profile.id, Service.is_deleted == False).count()
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

@router.put("/{service_id}", response_model=ServiceSchema)
def update_service(
    service_id: int,
    service_in: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_partner),
):
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first()
    service = db.query(Service).filter(Service.id == service_id, Service.is_deleted == False).first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found.")
    if service.partner_id != profile.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough privileges to update this service.")
    if profile.status in [PartnerStatus.SUSPENDED, PartnerStatus.BANNED]:
        raise HTTPException(status_code=403, detail="Suspended or banned partners cannot modify services.")
        
    update_data = service_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service, field, value)
        
    db.commit()
    db.refresh(service)
    return service

@router.delete("/{service_id}", response_model=dict)
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_partner),
):
    profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == current_user.id).first()
    service = db.query(Service).filter(Service.id == service_id, Service.is_deleted == False).first()
    
    if not service:
        raise HTTPException(status_code=404, detail="Service not found.")
    if service.partner_id != profile.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough privileges to delete this service.")
    if profile.status in [PartnerStatus.SUSPENDED, PartnerStatus.BANNED]:
        raise HTTPException(status_code=403, detail="Suspended or banned partners cannot modify services.")
        
    service.is_deleted = True
    db.commit()
    return {"detail": "Service deleted successfully."}

@router.get("/{service_id}", response_model=ServiceSchema)
def get_service(
    service_id: int, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    service = db.query(Service).options(
        joinedload(Service.city),
        joinedload(Service.category),
        joinedload(Service.partner)
    ).filter(Service.id == service_id, Service.is_deleted == False).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found.")
        
    result = ServiceSchema.model_validate(service)
    if not current_user:
        if result.partner:
            result.partner.phone = "HIDDEN_LOGIN_REQUIRED"
            result.partner.email = "HIDDEN_LOGIN_REQUIRED"
    return result
