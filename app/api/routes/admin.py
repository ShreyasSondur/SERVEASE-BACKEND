from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.api.dependencies import get_db, get_current_active_admin, get_current_active_mod
from app.models.user import User, UserRole
from app.models.partner import PartnerProfile, PartnerStatus
from app.models.catalog import Category, City, Emirate
from app.models.business import ActivityLog, Service, Deal
from app.models.analytics import SearchHistory
from app.schemas.partner import PartnerProfile as PartnerProfileSchema
from app.schemas.catalog import CategoryCreate, Category as CategorySchema, CityCreate, City as CitySchema, EmirateCreate

router = APIRouter()

# -----------------
# Dashboard (Mod & Admin)
# -----------------
@router.get("/dashboard", response_model=dict)
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_mod)):
    from app.models.business import Service, Deal
    users_count = db.query(User).filter(User.role == UserRole.USER).count()
    partners_count = db.query(PartnerProfile).count()
    services_count = db.query(Service).count()
    deals_count = db.query(Deal).count()
    
    return {
        "users": users_count + partners_count,
        "partners": partners_count,
        "services": services_count,
        "deals": deals_count
    }

# -----------------
# Partner Management (Mod & Admin)
# -----------------
@router.get("/partners", response_model=List[PartnerProfileSchema])
def list_partners(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_mod)):
    partners = db.query(PartnerProfile).options(joinedload(PartnerProfile.user)).offset(skip).limit(limit).all()
    return partners

@router.get("/partners/{partner_id}", response_model=PartnerProfileSchema)
def get_partner(partner_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_mod)):
    partner = db.query(PartnerProfile).filter(PartnerProfile.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    return partner

@router.patch("/verify/{partner_id}", response_model=PartnerProfileSchema)
def verify_partner(partner_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_mod)):
    partner = db.query(PartnerProfile).filter(PartnerProfile.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
        
    partner.status = PartnerStatus.VERIFIED
    partner.is_verified = True
    
    # Update the user's role to PARTNER so they get dashboard access
    user = db.query(User).filter(User.id == partner.user_id).first()
    if user and user.role == UserRole.USER:
        user.role = UserRole.PARTNER

    db.commit()
    db.refresh(partner)
    
    # Log action
    log = ActivityLog(user_id=current_user.id, action="VERIFY_PARTNER", description=f"Verified partner {partner_id}")
    db.add(log)
    db.commit()
    
    return partner

@router.patch("/suspend/{partner_id}", response_model=PartnerProfileSchema)
def suspend_partner(
    partner_id: int, 
    hours: int = Query(0, ge=0),
    days: int = Query(0, ge=0),
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_active_mod)
):
    partner = db.query(PartnerProfile).filter(PartnerProfile.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
        
    partner.status = PartnerStatus.SUSPENDED
    partner.is_verified = False
    
    if hours > 0 or days > 0:
        partner.suspended_until = datetime.now(timezone.utc) + timedelta(hours=hours, days=days)
    else:
        # Permanent suspension if no time specified
        partner.suspended_until = None
        
    db.commit()
    db.refresh(partner)
    
    # Log action
    log = ActivityLog(user_id=current_user.id, action="SUSPEND_PARTNER", description=f"Suspended partner {partner_id} for {days} days, {hours} hours")
    db.add(log)
    db.commit()
    
    return partner

@router.patch("/ban/{partner_id}", response_model=PartnerProfileSchema)
def ban_partner(partner_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_mod)):
    partner = db.query(PartnerProfile).filter(PartnerProfile.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
        
    partner.status = PartnerStatus.BANNED
    partner.is_verified = False
    partner.suspended_until = None
    db.commit()
    db.refresh(partner)
    
    log = ActivityLog(user_id=current_user.id, action="BAN_PARTNER", description=f"Banned partner {partner_id}")
    db.add(log)
    db.commit()
    
    return partner

# -----------------
# User Management (Admin Only)
# -----------------
@router.get("/users")
def list_users(db: Session = Depends(get_db), current_admin: User = Depends(get_current_active_admin)):
    users = db.query(User).filter(User.role.in_([UserRole.USER, UserRole.PARTNER])).all()
    return [{
        "id": u.id,
        "email": u.email,
        "full_name": u.full_name,
        "is_active": u.is_active,
        "phone_number": u.phone_number,
        "role": u.role.value if hasattr(u.role, 'value') else u.role,
        "created_at": u.created_at.isoformat() if u.created_at else None
    } for u in users]

# -----------------
# Mod Management (Admin Only)
# -----------------
@router.get("/mods")
def list_mods(db: Session = Depends(get_db), current_admin: User = Depends(get_current_active_admin)):
    mods = db.query(User).filter(User.role == UserRole.MODERATOR).all()
    return [{"id": m.id, "email": m.email, "full_name": m.full_name, "is_active": m.is_active, "is_banned": m.is_banned} for m in mods]

@router.patch("/mods/verify/{mod_id}")
def verify_mod(mod_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_active_admin)):
    mod = db.query(User).filter(User.id == mod_id, User.role == UserRole.MODERATOR).first()
    if not mod:
        raise HTTPException(status_code=404, detail="Moderator not found")
    mod.is_active = True
    mod.is_banned = False
    db.commit()
    
    log = ActivityLog(user_id=current_admin.id, action="VERIFY_MOD", description=f"Verified moderator {mod_id}")
    db.add(log)
    db.commit()
    
    return {"message": "Moderator verified successfully"}

@router.patch("/mods/ban/{mod_id}")
def ban_mod(mod_id: int, db: Session = Depends(get_db), current_admin: User = Depends(get_current_active_admin)):
    mod = db.query(User).filter(User.id == mod_id, User.role == UserRole.MODERATOR).first()
    if not mod:
        raise HTTPException(status_code=404, detail="Moderator not found")
        
    # Toggle ban status
    mod.is_banned = not mod.is_banned
    if mod.is_banned:
        mod.is_active = False # Disable login if banned
        action = "BAN_MOD"
        desc = f"Banned moderator {mod_id}"
    else:
        # Unbanning doesn't automatically verify, but let's make them inactive so they need verify, or active?
        # Actually if they were active before ban, maybe active. Let's set active.
        mod.is_active = True
        action = "UNBAN_MOD"
        desc = f"Unbanned moderator {mod_id}"
        
    db.commit()
    
    log = ActivityLog(user_id=current_admin.id, action=action, description=desc)
    db.add(log)
    db.commit()
    
    return {"message": desc}

# -----------------
# Catalog Management (Admin Only)
# -----------------
@router.post("/categories", response_model=CategorySchema)
def add_category(cat: CategoryCreate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_active_admin)):
    db_cat = Category(name=cat.name, description=cat.description)
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat

@router.post("/emirates", response_model=dict)
def add_emirate(emirate: EmirateCreate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_active_admin)):
    from app.models.catalog import Emirate
    db_em = Emirate(name=emirate.name)
    db.add(db_em)
    db.commit()
    db.refresh(db_em)
    return {"id": db_em.id, "name": db_em.name}

@router.post("/cities", response_model=CitySchema)
def add_city(city: CityCreate, db: Session = Depends(get_db), current_admin: User = Depends(get_current_active_admin)):
    db_city = City(name=city.name, emirate_id=city.emirate_id)
    db.add(db_city)
    db.commit()
    db.refresh(db_city)
    return db_city

@router.delete("/categories/{category_id}", response_model=dict)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Delete associated deals
    db.query(Deal).filter(Deal.category_id == category_id).delete(synchronize_session=False)
        
    # Delete associated services
    db.query(Service).filter(Service.category_id == category_id).delete(synchronize_session=False)
    
    # Nullify SearchHistory category references
    db.query(SearchHistory).filter(SearchHistory.category_id == category_id).update({SearchHistory.category_id: None}, synchronize_session=False)
    
    # Delete the category
    db.delete(category)
    db.commit()
    
    # Log action
    log = ActivityLog(user_id=current_admin.id, action="DELETE_CATEGORY", description=f"Deleted category '{category.name}' (ID: {category_id})")
    db.add(log)
    db.commit()
    
    return {"detail": "Category deleted successfully"}

@router.delete("/emirates/{emirate_id}", response_model=dict)
def delete_emirate(
    emirate_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    emirate = db.query(Emirate).filter(Emirate.id == emirate_id).first()
    if not emirate:
        raise HTTPException(status_code=404, detail="Emirate not found")
        
    # Cascade: Get all cities under this emirate
    cities = db.query(City).filter(City.emirate_id == emirate_id).all()
    city_ids = [c.id for c in cities]
    
    # Delete associated deals
    if city_ids:
        db.query(Deal).filter(Deal.city_id.in_(city_ids)).delete(synchronize_session=False)
        
    # Delete associated services
    if city_ids:
        db.query(Service).filter(Service.city_id.in_(city_ids)).delete(synchronize_session=False)
        
    # Nullify SearchHistory emirate and city references
    db.query(SearchHistory).filter(SearchHistory.emirate_id == emirate_id).update({SearchHistory.emirate_id: None}, synchronize_session=False)
    if city_ids:
        db.query(SearchHistory).filter(SearchHistory.city_id.in_(city_ids)).update({SearchHistory.city_id: None}, synchronize_session=False)
        
    # Delete cities under this emirate
    db.query(City).filter(City.emirate_id == emirate_id).delete(synchronize_session=False)
    
    # Delete the emirate
    db.delete(emirate)
    db.commit()
    
    # Log action
    log = ActivityLog(user_id=current_admin.id, action="DELETE_EMIRATE", description=f"Deleted emirate '{emirate.name}' (ID: {emirate_id})")
    db.add(log)
    db.commit()
    
    return {"detail": "Emirate deleted successfully"}

@router.put("/emirates/{emirate_id}/toggle-visibility", response_model=dict)
def toggle_emirate_visibility(
    emirate_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    from app.models.catalog import Emirate
    emirate = db.query(Emirate).filter(Emirate.id == emirate_id).first()
    if not emirate:
        raise HTTPException(status_code=404, detail="Emirate not found")
    emirate.is_visible = not emirate.is_visible
    db.commit()
    db.refresh(emirate)
    
    # Log action
    log = ActivityLog(user_id=current_admin.id, action="TOGGLE_EMIRATE_VISIBILITY", description=f"Toggled visibility of emirate '{emirate.name}' (ID: {emirate_id}) to {emirate.is_visible}")
    db.add(log)
    db.commit()
    
    return {"id": emirate.id, "name": emirate.name, "is_visible": emirate.is_visible}

@router.delete("/cities/{city_id}", response_model=dict)
def delete_city(
    city_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_active_admin)
):
    city = db.query(City).filter(City.id == city_id).first()
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
        
    # Delete associated deals
    db.query(Deal).filter(Deal.city_id == city_id).delete(synchronize_session=False)
        
    # Delete associated services
    db.query(Service).filter(Service.city_id == city_id).delete(synchronize_session=False)
    
    # Nullify SearchHistory city references
    db.query(SearchHistory).filter(SearchHistory.city_id == city_id).update({SearchHistory.city_id: None}, synchronize_session=False)
    
    # Delete the city
    db.delete(city)
    db.commit()
    
    # Log action
    log = ActivityLog(user_id=current_admin.id, action="DELETE_CITY", description=f"Deleted city '{city.name}' (ID: {city_id})")
    db.add(log)
    db.commit()
    
    return {"detail": "City deleted successfully"}

# -----------------
# Analytics & Logs (Admin Only)
# -----------------
@router.get("/search-history")
def get_search_history(
    time_period: Optional[str] = None,
    emirate: Optional[str] = None,
    db: Session = Depends(get_db), 
    current_admin: User = Depends(get_current_active_admin)
):
    query = db.query(SearchHistory).options(
        joinedload(SearchHistory.user),
        joinedload(SearchHistory.category),
        joinedload(SearchHistory.emirate),
        joinedload(SearchHistory.city)
    ).join(User, SearchHistory.user_id == User.id, isouter=True).filter(
        (SearchHistory.user_role != "ADMIN") | (SearchHistory.user_role.is_(None)),
        (User.role != UserRole.ADMIN) | (User.role.is_(None))
    )
    
    if time_period:
        now = datetime.now(timezone.utc)
        if time_period == "Today":
            query = query.filter(SearchHistory.timestamp >= now.replace(hour=0, minute=0, second=0, microsecond=0))
        elif time_period == "This Week":
            query = query.filter(SearchHistory.timestamp >= now - timedelta(days=7))
        elif time_period == "This Month":
            query = query.filter(SearchHistory.timestamp >= now - timedelta(days=30))
        elif time_period == "This Year":
            query = query.filter(SearchHistory.timestamp >= now - timedelta(days=365))
            
    if emirate and emirate != "All":
        query = query.join(Emirate).filter(Emirate.name.ilike(f"%{emirate}%"))
        
    searches = query.all()
    return [{
        "id": s.id,
        "user_id": s.user_id,
        "user_role": s.user_role or (s.user.role.value if s.user else "Guest"),
        "username": s.username or (s.user.full_name if s.user else "Guest"),
        "email": s.email or (s.user.email if s.user else "Guest"),
        "phone": s.phone or (s.user.phone_number if s.user else "Guest"),
        "query": s.search_query,
        "category": s.category.name if s.category else "",
        "emirate": s.emirate.name if s.emirate else "",
        "city": s.city.name if s.city else "",
        "timestamp": s.timestamp
    } for s in searches]

@router.get("/activity-logs")
def get_activity_logs(db: Session = Depends(get_db), current_admin: User = Depends(get_current_active_admin)):
    import re
    logs = db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).all()
    result = []
    for l in logs:
        actor_name = "System"
        actor_id = None
        actor_role = None
        
        if l.user_id:
            user = db.query(User).filter(User.id == l.user_id).first()
            if user:
                actor_id = user.id
                actor_role = user.role.value if hasattr(user.role, 'value') else str(user.role)
                if user.role == UserRole.ADMIN:
                    actor_name = "Admin"
                elif user.role == UserRole.MODERATOR:
                    actor_name = user.email
                else:
                    actor_name = user.email
                    
        # Extract target partner name and ID if applicable
        target_partner_name = None
        target_partner_id = None
        
        if l.action in ["VERIFY_PARTNER", "SUSPEND_PARTNER", "BAN_PARTNER"]:
            match = re.search(r"partner (\d+)", l.description or "")
            if match:
                pid = int(match.group(1))
                target_partner_id = pid
                partner = db.query(PartnerProfile).filter(PartnerProfile.id == pid).first()
                if partner:
                    target_partner_name = partner.business_name or f"{partner.first_name} {partner.last_name}"
                    
        result.append({
            "id": l.id,
            "user_id": l.user_id,
            "action": l.action,
            "description": l.description,
            "timestamp": l.timestamp,
            "actor_name": actor_name,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "target_partner_name": target_partner_name,
            "target_partner_id": target_partner_id
        })
    return result
