from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user
from app.core import security
from app.core.config import settings
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, User as UserSchema
from app.schemas.token import Token, VerifyOTP, ResendOTP
from jose import jwt
from datetime import datetime, timezone
import random
import string
from app.utils.email import send_otp_email

router = APIRouter()

@router.post("/admin/signup", response_model=UserSchema)
def create_mod(user_in: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    # Moderators are created inactive until an Admin verifies them
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        password_hash=security.get_password_hash(user_in.password),
        role=UserRole.MODERATOR,
        is_active=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/signup", response_model=UserSchema)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        password_hash=security.get_password_hash(user_in.password),
        role=UserRole.USER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif user.is_banned:
        raise HTTPException(status_code=403, detail="Account is banned")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Check if the user is an ADMIN
    if user.role == UserRole.ADMIN:
        # Generate 6-digit OTP
        otp = "".join(random.choices(string.digits, k=6))
        user.otp_code = otp
        user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        db.commit()
        
        # Send OTP email
        send_otp_email(settings.ADMIN_OTP_EMAIL, otp)
        
        # Create temp_token for OTP verification page session
        expire = datetime.now(timezone.utc) + timedelta(minutes=10)
        to_encode = {"exp": expire, "sub": str(user.id), "type": "temp_otp"}
        temp_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        return {
            "requires_otp": True,
            "temp_token": temp_token
        }
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/verify-otp", response_model=Token)
def verify_otp(data: VerifyOTP, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(data.temp_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_type = payload.get("type")
        if token_type != "temp_otp":
            raise HTTPException(status_code=400, detail="Invalid token type")
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired temporary session")
        
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.otp_code or user.otp_code != data.otp:
        raise HTTPException(status_code=400, detail="Incorrect OTP")
        
    otp_expires = user.otp_expires_at
    if otp_expires:
        if otp_expires.tzinfo is None:
            otp_expires = otp_expires.replace(tzinfo=timezone.utc)
        if otp_expires < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="OTP has expired")
            
    # Clear OTP
    user.otp_code = None
    user.otp_expires_at = None
    db.commit()
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/resend-otp")
def resend_otp(data: ResendOTP, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(data.temp_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_type = payload.get("type")
        if token_type != "temp_otp":
            raise HTTPException(status_code=400, detail="Invalid token type")
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired temporary session")
        
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Generate new OTP
    otp = "".join(random.choices(string.digits, k=6))
    user.otp_code = otp
    user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    db.commit()
    
    # Send email
    send_otp_email(settings.ADMIN_OTP_EMAIL, otp)
    
    return {"message": "OTP resent successfully"}

@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

from pydantic import BaseModel

class PhoneUpdate(BaseModel):
    phone_number: str

@router.put("/me/phone", response_model=UserSchema)
def update_phone_number(data: PhoneUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.phone_number = data.phone_number
    db.commit()
    db.refresh(current_user)
    return current_user

import httpx
from fastapi.responses import RedirectResponse
import secrets

@router.get("/google/login")
def google_login(prompt: str = None):
    client_id = settings.GOOGLE_CLIENT_ID
    if not client_id:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
        
    # Using frontend redirect URI for now, or backend
    redirect_uri = f"{settings.SERVER_HOST}/api/v1/auth/google/callback"
    
    google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={client_id}&redirect_uri={redirect_uri}&scope=openid%20email%20profile&access_type=offline"
    
    if prompt:
        google_auth_url += f"&prompt={prompt}"
        
    return RedirectResponse(google_auth_url)

@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    client_id = settings.GOOGLE_CLIENT_ID
    client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', '')
    redirect_uri = f"{settings.SERVER_HOST}/api/v1/auth/google/callback"

    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_res.status_code != 200:
            error_details = token_res.text
            raise HTTPException(status_code=400, detail=f"Failed to authenticate with Google: {error_details}")
            
        token_data = token_res.json()
        
        # Get user info
        user_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )
        user_info = user_res.json()
        
        email = user_info.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Google account has no email")
            
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # Create user
            random_pass = secrets.token_urlsafe(32)
            user = User(
                email=email,
                password_hash=security.get_password_hash(random_pass),
                role=UserRole.USER,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
        
        # Redirect back to frontend with token
        return RedirectResponse(f"{settings.FRONTEND_HOST}/login?token={token}")
