import os
from sqlalchemy.orm import Session
from app.db.session import engine, SessionLocal
from app.db.base_class import Base
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from app.core.config import settings

def init_db(db: Session) -> None:
    # Ensure tables are created
    Base.metadata.create_all(bind=engine)
    
    # Check if admin already exists
    admin_user = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
    if not admin_user:
        print(f"Creating admin user with email: {settings.ADMIN_EMAIL}")
        user = User(
            email=settings.ADMIN_EMAIL,
            password_hash=get_password_hash(settings.ADMIN_PASSWORD),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print("Admin user created successfully.")
    else:
        print("Admin user already exists.")

if __name__ == "__main__":
    print("Initializing Database...")
    db = SessionLocal()
    init_db(db)
    db.close()
    print("Database initialization complete.")
