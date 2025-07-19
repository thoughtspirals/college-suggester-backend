# app/scripts/load_regions.py

from app.database import SessionLocal
from app.models import College

def extract_region(name: str) -> str:
    parts = name.split(",")
    return parts[-1].strip() if len(parts) > 1 else ""

def update_regions():
    db = SessionLocal()
    try:
        colleges = db.query(College).all()
        for college in colleges:
            region = extract_region(college.name)
            college.region = region
        db.commit()
        print("✅ Region field updated for all colleges.")
    except Exception as e:
        print("❌ Error updating regions:", e)
    finally:
        db.close()

if __name__ == "__main__":
    update_regions()
