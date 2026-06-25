from app.db.session import SessionLocal, engine
from app.db.base_class import Base
from app.models.user import User, UserRole
from app.models.partner import PartnerProfile, PartnerStatus
from app.models.catalog import Category, Emirate, City
from app.models.business import Service, Deal
from app.core.security import get_password_hash
from app.core.config import settings
from datetime import datetime, timedelta, timezone

def seed():
    # Recreate tables to ensure schema matches perfectly
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        print("Seeding admin...")
        admin = db.query(User).filter(User.email == "admin@servease.com").first()
        if not admin:
            admin = User(
                email="admin@servease.com",
                password_hash=get_password_hash("admin123"),
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin)
            db.commit()

        print("Seeding testing users...")
        client_user = db.query(User).filter(User.email == "user@servease.com").first()
        if not client_user:
            client_user = User(
                email="user@servease.com",
                password_hash=get_password_hash("user123"),
                role=UserRole.USER,
                is_active=True
            )
            db.add(client_user)

        partner_user = db.query(User).filter(User.email == "partner@servease.com").first()
        if not partner_user:
            partner_user = User(
                email="partner@servease.com",
                password_hash=get_password_hash("partner123"),
                role=UserRole.PARTNER,
                is_active=True
            )
            db.add(partner_user)
            db.commit()
            db.refresh(partner_user)

        print("Seeding catalog...")
        # Categories
        ac_repair = db.query(Category).filter(Category.name == "AC Repair").first()
        if not ac_repair:
            ac_repair = Category(name="AC Repair", description="AC maintenance and repair")
            plumbing = Category(name="Plumbing", description="Professional plumbing fixes")
            electrical = Category(name="Electrical", description="Electrical wiring and installations")
            cleaning = Category(name="Cleaning", description="Deep cleaning and sanitization")
            db.add_all([ac_repair, plumbing, electrical, cleaning])
            db.commit()
            db.refresh(ac_repair)
        else:
            plumbing = db.query(Category).filter(Category.name == "Plumbing").first()
            electrical = db.query(Category).filter(Category.name == "Electrical").first()
            cleaning = db.query(Category).filter(Category.name == "Cleaning").first()

        # Emirates & Cities
        dubai = db.query(Emirate).filter(Emirate.name == "Dubai").first()
        if not dubai:
            dubai = Emirate(name="Dubai")
            abudhabi = Emirate(name="Abu Dhabi")
            db.add_all([dubai, abudhabi])
            db.commit()
            db.refresh(dubai)
            
            c1 = City(name="Downtown Dubai", emirate_id=dubai.id)
            c2 = City(name="Dubai Marina", emirate_id=dubai.id)
            c3 = City(name="Jumeirah", emirate_id=dubai.id)
            c4 = City(name="Al Reem Island", emirate_id=abudhabi.id)
            db.add_all([c1, c2, c3, c4])
            db.commit()
        
        city_downtown = db.query(City).filter(City.name == "Downtown Dubai").first()
        city_marina = db.query(City).filter(City.name == "Dubai Marina").first()

        print("Seeding partner profile...")
        profile = db.query(PartnerProfile).filter(PartnerProfile.user_id == partner_user.id).first()
        if not profile:
            profile = PartnerProfile(
                user_id=partner_user.id,
                first_name="John",
                last_name="Doe",
                phone="+971501234567",
                emirate="Dubai",
                city="Downtown Dubai",
                emirate_id_number="784-1990-1234567-1",
                business_name="Servease Pro Services",
                emirates_id_url="https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg",
                is_verified=True,
                status=PartnerStatus.VERIFIED,
                services_limit=6,
                deals_limit=2
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)

        print("Seeding services...")
        s1 = db.query(Service).filter(Service.title == "Premium AC Deep Cleaning & Disinfection").first()
        if not s1:
            s1 = Service(
                partner_id=profile.id,
                category_id=ac_repair.id,
                city_id=city_downtown.id,
                title="Premium AC Deep Cleaning & Disinfection",
                description="Keep your air clean and healthy. We provide a full deep cleaning of coils, filters, drain trays, and blowers. Includes disinfection to eliminate bacteria and mold. Standard rates apply for additional parts.",
                images=[
                    "https://images.unsplash.com/photo-1621905251189-08b45d6a269e?w=800&auto=format&fit=crop",
                    "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=800&auto=format&fit=crop",
                    "https://images.unsplash.com/photo-1581092921461-eab62e97a780?w=800&auto=format&fit=crop",
                    "https://images.unsplash.com/photo-1621905252507-b354bc25edac?w=800&auto=format&fit=crop"
                ],
                emergency_service="Available 24/7",
                provider_type="Licensed Company",
                is_active=True
            )
            s2 = Service(
                partner_id=profile.id,
                category_id=plumbing.id,
                city_id=city_marina.id,
                title="Emergency Pipe Leak Fix & Drainage Unclogging",
                description="Got a pipe burst or blocked toilet? Our expert plumbers are ready to help. We diagnose and fix water line leaks, drain line blockages, and install fixtures quickly.",
                images=[
                    "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=800&auto=format&fit=crop",
                    "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=800&auto=format&fit=crop"
                ],
                emergency_service="Available 24/7",
                provider_type="Licensed Company",
                is_active=True
            )
            db.add_all([s1, s2])
            db.commit()

        print("Seeding standalone deals...")
        d1 = db.query(Deal).filter(Deal.title == "30% OFF AC Deep Cleaning Special").first()
        if not d1:
            d1 = Deal(
                partner_id=profile.id,
                category_id=ac_repair.id,
                city_id=city_downtown.id,
                title="30% OFF AC Deep Cleaning Special",
                description="Get a premium cooling system service and deep sanitization for 30% OFF. Refresh your indoor air quality and lower your cooling bills today!",
                images=[
                    "https://images.unsplash.com/photo-1621905251189-08b45d6a269e?w=800&auto=format&fit=crop",
                    "https://images.unsplash.com/photo-1581092921461-eab62e97a780?w=800&auto=format&fit=crop"
                ],
                discount_desc="30% OFF AC Cleaning",
                expiry_date=datetime.now(timezone.utc) + timedelta(days=30),
                is_active=True
            )
            db.add(d1)
            db.commit()

        print("Full database seeding complete.")
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
