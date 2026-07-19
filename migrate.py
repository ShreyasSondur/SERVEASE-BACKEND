from app.db.session import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        conn.execute(text('ALTER TABLE ad_configs ADD COLUMN redirect_url VARCHAR;'))
        conn.commit()
    print("Migration successful")
except Exception as e:
    print(f"Migration failed or already applied: {e}")
