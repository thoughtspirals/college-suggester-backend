from app.database import SessionLocal
from app.models import Cutoff
from app.database import engine

with SessionLocal() as db:
    count = db.query(Cutoff).count()
    print("📦 DB Path:", engine.url)
    print(f"✅ Total records in database: {count}")
