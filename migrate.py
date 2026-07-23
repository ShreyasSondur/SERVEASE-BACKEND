from app.db.session import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        for col in ["user_role", "username", "email", "phone"]:
            try:
                conn.execute(text(f'ALTER TABLE search_history ADD COLUMN {col} VARCHAR;'))
                conn.commit()
                print(f"Migration successful: added {col} to search_history")
            except Exception as e:
                print(f"Migration failed or already applied for {col}: {e}")
except Exception as e:
    print(f"Database connection failed: {e}")
