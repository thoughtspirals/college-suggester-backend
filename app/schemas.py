from pydantic import BaseModel
from typing import Optional

class CutoffOut(BaseModel):
    college: str
    branch: str
    category: str
    rank: int
    percent: Optional[float]
    gender: str
    level: str

    class Config:
        orm_mode = True


class CollegeSuggestionRequest(BaseModel):
    """Request schema for college suggestion API"""
    rank: int
    caste: str  # e.g., "OPEN", "OBC", "SC", "ST", "EWS", "NT1", "NT2", "NT3", "SBC", "SEBC", "VJ"
    gender: str  # "MALE" or "FEMALE"
    seat_type: str  # "H" (Home), "O" (Other), "S" (State), "AI" (All India)
    special_reservation: Optional[str] = None  # "PWD", "DEFENCE", "ORPHAN", "TFWS"


class CollegeSuggestionResponse(BaseModel):
    """Response schema for college suggestion API"""
    college: str
    branch: str
    category: str
    rank: int  # This is the cutoff rank
    percent: Optional[float]
    gender: str
    level: str
    year: int
    stage: str

    class Config:
        orm_mode = True


class CollegeStatistics(BaseModel):
    """Statistics about available colleges"""
    total_colleges: int
    total_branches: int
    unique_colleges: int
    seat_types: list[str]
    categories: list[str]
    rank_range: Optional[dict] = None
