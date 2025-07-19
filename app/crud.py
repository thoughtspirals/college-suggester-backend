from sqlalchemy.orm import Session
from app import models

def get_top_colleges(db: Session, rank: int, caste: str, gender: str, limit=5):
    query = db.query(models.Cutoff).filter(
        models.Cutoff.category.contains(caste.upper()),
        models.Cutoff.rank >= rank
    )
    if gender.lower() == "female":
        query = query.filter(models.Cutoff.category.contains("L"))
    return query.order_by(models.Cutoff.rank.asc()).limit(limit).all()
