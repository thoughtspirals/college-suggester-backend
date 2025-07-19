from app.database import SessionLocal
from app.models import Cutoff

db = SessionLocal()

cutoff = Cutoff(
    college="Test College",
    branch="Computer Engineering",
    category="GOPENH",
    rank=12345,
    percent=89.56,
    gender="male",
    level="home"
)

db.add(cutoff)
db.commit()
print("✅ Inserted test record.")
