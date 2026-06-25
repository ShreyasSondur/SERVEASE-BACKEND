from app.db.session import SessionLocal
from app.models.catalog import Category, Emirate, City

def seed():
    db = SessionLocal()
    try:
        # Check if category exists
        if db.query(Category).count() == 0:
            print("Seeding categories...")
            ac = Category(name="AC Repair", description="Air Conditioning maintenance and repair")
            plumbing = Category(name="Plumbing", description="Plumbing and pipe fixing services")
            electrical = Category(name="Electrical", description="Electrical wiring and fixture maintenance")
            db.add_all([ac, plumbing, electrical])
            db.commit()

        # Check if emirates exist
        if db.query(Emirate).count() == 0:
            print("Seeding emirates and cities...")
            dubai = Emirate(name="Dubai")
            abudhabi = Emirate(name="Abu Dhabi")
            db.add_all([dubai, abudhabi])
            db.commit()

            # Seed cities
            c1 = City(name="Downtown Dubai", emirate_id=dubai.id)
            c2 = City(name="Dubai Marina", emirate_id=dubai.id)
            c3 = City(name="Al Reem Island", emirate_id=abudhabi.id)
            db.add_all([c1, c2, c3])
            db.commit()
            
        print("Catalog seeding complete.")
    except Exception as e:
        print(f"Error seeding catalog: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
