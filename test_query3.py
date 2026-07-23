from app.db.session import SessionLocal; from app.api.routes.admin import get_dashboard_stats; db = SessionLocal(); print(get_dashboard_stats(db=db, current_user=None))
