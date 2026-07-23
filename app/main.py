from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.base_class import Base
from app.db.session import engine
from app.api.routes import auth, partner, services, deals, search, admin, catalog, contact, ads

# Create database tables (For production, Alembic is recommended)
Base.metadata.create_all(bind=engine)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database columns for OTP exist
    from app.db.session import engine
    from sqlalchemy import text
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_code VARCHAR;"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS otp_expires_at TIMESTAMP;"))
    except Exception as e:
        print(f"Error altering users table: {e}")

    # Initialize Admin User on startup
    from app.db.session import SessionLocal
    from app.models.user import User, UserRole
    from app.core.security import get_password_hash
    
    db = SessionLocal()
    admin_user = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
    if not admin_user:
        user = User(
            email=settings.ADMIN_EMAIL,
            password_hash=get_password_hash(settings.ADMIN_PASSWORD),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(user)
        db.commit()
    db.close()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
      allow_origins=[
          settings.FRONTEND_HOST,
          "http://localhost:3000",
          "http://127.0.0.1:3000",
          "http://localhost:3001",
          "http://127.0.0.1:3001",
          "https://www.servizuae.com",
          "https://servizuae.com"
      ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(partner.router, prefix=f"{settings.API_V1_STR}/partner", tags=["partner"])
app.include_router(services.router, prefix=f"{settings.API_V1_STR}/services", tags=["services"])
app.include_router(deals.router, prefix=f"{settings.API_V1_STR}/deals", tags=["deals"])
app.include_router(search.router, prefix=f"{settings.API_V1_STR}/search", tags=["search"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
app.include_router(catalog.router, prefix=f"{settings.API_V1_STR}/catalog", tags=["catalog"])
app.include_router(contact.router, prefix=f"{settings.API_V1_STR}/contact", tags=["contact"])
app.include_router(ads.router, prefix=f"{settings.API_V1_STR}/ads", tags=["ads"])

@app.get("/")
def root():
    return {"message": "Welcome to Dubai Services & Deals Platform API"}
