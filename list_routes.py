from app.main import app; print([r.path for r in app.routes if "admin" in r.path])
