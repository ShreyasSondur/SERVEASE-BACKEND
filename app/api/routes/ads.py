from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_active_admin
from app.models.ads import AdConfig
from app.schemas.ads import AdConfigResponse, AdConfigUpdate

router = APIRouter()

@router.get("/", response_model=List[AdConfigResponse])
def get_ads(db: Session = Depends(get_db)):
    """
    Get all ad configurations.
    """
    ads = db.query(AdConfig).all()
    # If no ads exist yet, return an empty list or create defaults. Let's return what we have.
    return ads

@router.patch("/{position}", response_model=AdConfigResponse)
def update_ad(
    position: str,
    ad_in: AdConfigUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_active_admin)
):
    """
    Update an ad configuration by position (e.g. 'add1', 'add2').
    """
    ad = db.query(AdConfig).filter(AdConfig.position == position).first()
    
    if not ad:
        # Create it if it doesn't exist
        ad = AdConfig(position=position)
        db.add(ad)
        db.commit()
        db.refresh(ad)

    if ad_in.image_url is not None:
        ad.image_url = ad_in.image_url
    if ad_in.redirect_url is not None:
        ad.redirect_url = ad_in.redirect_url
    if ad_in.is_active is not None:
        ad.is_active = ad_in.is_active

    db.commit()
    db.refresh(ad)
    return ad
