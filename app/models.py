from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from sqlalchemy import UniqueConstraint

class College(Base):
    __tablename__ = "colleges"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(Integer)  # e.g., 1150
    name = Column(String)
    status = Column(String)  # e.g., 'Government', 'Private', 'Aided'
    university = Column(String)
    region = Column(String)
     
    # Relationship with cutoffs
    cutoffs = relationship("Cutoff", back_populates="college")
    
    __table_args__ = (
        UniqueConstraint('code', 'name', 'status', name='unique_college_code_name_status'),
    )

class Cutoff(Base):
    __tablename__ = "cutoffs"

    id = Column(Integer, primary_key=True, index=True)
    college_id = Column(Integer, ForeignKey('colleges.id'), nullable=False)
    college_code = Column(Integer, nullable=False)
    branch = Column(String)
    course_code = Column(Integer, nullable=False)
    category = Column(String)
    rank = Column(Integer, nullable=True)
    percent = Column(Float, nullable=True)
    gender = Column(String)
    level = Column(String)  # Home/Other/State level
    year = Column(Integer, nullable=True)
    stage = Column(String, nullable=True)
    
    # Relationship with college
    college = relationship("College", back_populates="cutoffs")

class RankedCollege(Base):
    __tablename__ = "ranked_colleges"

    id = Column(Integer, primary_key=True, index=True)
    college_id = Column(Integer, nullable=False)
    college_code = Column(Integer, nullable=False)
    college_name = Column(String, nullable=False)
    college_status = Column(String, nullable=True)
    branch = Column(String, nullable=False)  # Normalized branch name
    branch_code = Column(String, nullable=False)
    cutoff_rank = Column(Integer, nullable=False)
    rank_position = Column(Integer, nullable=False)
    year = Column(Integer, nullable=True)
    stage = Column(String, nullable=True)
