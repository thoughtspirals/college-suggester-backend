from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, Integer
from app.models import Cutoff, College
from app.schemas import CutoffOut
from pydantic import BaseModel


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
    cutoff_rank: int
    percent: Optional[float]
    gender: str
    level: str
    year: int
    stage: str

    class Config:
        orm_mode = True


def get_suggested_colleges(
    db: Session,
    rank: int,
    caste: str,
    gender: str,
    seat_type: str,
    special_reservation: Optional[str] = None,
    limit: int = 20
) -> List[Cutoff]:
    """
    Get top 20 colleges based on student's rank and preferences.
    
    Args:
        db: Database session
        rank: Student's CET rank
        caste: Student's caste category (OPEN, OBC, SC, ST, EWS, NT1, NT2, NT3, SBC, SEBC, VJ)
        gender: Student's gender (MALE, FEMALE)
        seat_type: Type of seat (H-Home, O-Other, S-State, AI-All India)
        special_reservation: Special reservation type (PWD, DEFENCE, ORPHAN, TFWS)
        limit: Maximum number of colleges to return (default 20)
        
    Returns:
        List of colleges with cutoff ranks greater than or equal to student's rank,
        sorted by cutoff rank (lowest first)
    """
    
    # Normalize inputs
    caste = caste.upper().strip()
    gender = gender.upper().strip()
    seat_type = seat_type.upper().strip()
    
    # Build base query with join to get college name
    query = db.query(Cutoff).join(College).filter(
        Cutoff.rank >= rank,  # Student's rank should be better than or equal to cutoff (student can get admission)
        Cutoff.rank.isnot(None)  # Exclude null ranks
    )
    
    # Filter by seat type/level
    seat_type_mapping = {
        "H": "home",
        "O": "other", 
        "S": "state",
        "AI": "all india"
    }
    
    if seat_type in seat_type_mapping:
        query = query.filter(Cutoff.level.contains(seat_type_mapping[seat_type]))

    # Construct category filter based on the database pattern
    # Format: [GENDER][CASTE][SEAT_TYPE] or [SPECIAL_RESERVATION][GENDER][CASTE][SEAT_TYPE] or TFWS
    # Examples: GOPENS, GOBCS, LOPENS, LSEBCS, GNT2S, GNT3S, TFWS, etc.
    
    gender_code = 'G' if gender == 'MALE' else 'L'
    
    # Map seat types to their database codes
    seat_type_code_mapping = {
        "H": "H",
        "O": "O", 
        "S": "S",
        "AI": "AI"
    }
    
    seat_type_code = seat_type_code_mapping.get(seat_type, "S")
    
    # Handle special reservations
    if special_reservation:
        special_code = special_reservation.upper()
        # Handle special cases for PWD variants
        if special_code == 'PWD':
            # PWD can be stored as PWD or PWDR in database (no gender code)
            category_patterns = [
                f"PWD{caste}{seat_type_code}",
                f"PWDR{caste}{seat_type_code}"
            ]
        elif special_code == 'DEFENCE':
            # DEFENCE can be stored as DEF or DEFR in database (no gender code)
            category_patterns = [
                f"DEFR{caste}{seat_type_code}",
                f"DEF{caste}{seat_type_code}"
            ]
        elif special_code == 'ORPHAN':
            # ORPHAN is stored as just "ORPHAN"
            category_patterns = [
                f"ORPHAN"
            ]
        elif special_code == 'TFWS':
            # TFWS is stored as just "TFWS"
            category_patterns = [
                f"TFWS"
            ]
        else:
            # Other special reservations (no gender code)
            category_patterns = [
                f"{special_code}{caste}{seat_type_code}"
            ]
    else:
        # Regular category without special reservation
        category_patterns = [
            f"{gender_code}{caste}{seat_type_code}"
        ]
    
    # Apply category filter with OR condition for multiple patterns
    category_filters = []
    for pattern in category_patterns:
        category_filters.append(Cutoff.category.like(f"%{pattern}%"))
    
    if category_filters:
        query = query.filter(or_(*category_filters))
    
    # Order by cutoff rank (lowest first) and limit results
    result = query.order_by(Cutoff.rank.asc()).limit(limit).all()
    
    return result


def get_college_details_by_rank(
    db: Session,
    rank: int,
    caste: str,
    gender: str,
    seat_type: str,
    college_name: Optional[str] = None,
    branch: Optional[str] = None,
    special_reservation: Optional[str] = None,
    limit: int = 50
) -> List[Cutoff]:
    """
    Get detailed cutoff information for specific college/branch combination.
    Uses normalized branch names from ranked_colleges table for better search.
    
    Args:
        db: Database session
        rank: Student's CET rank
        caste: Student's caste category
        gender: Student's gender
        seat_type: Type of seat
        college_name: Specific college name (optional)
        branch: Specific branch name - can be normalized (like 'CS') or full name (optional)
        special_reservation: Special reservation type (optional)
        
    Returns:
        List of matching cutoff records
    """
    
    # Start with base filters - join with College and optionally RankedCollege for normalized branch names
    query = db.query(Cutoff).join(College).filter(
        Cutoff.rank >= rank,  # Use same logic as get_suggested_colleges
        Cutoff.rank.isnot(None)
    )
    
    # Apply filters from get_suggested_colleges
    if college_name:
        query = query.filter(College.name.contains(college_name))
    
    # Enhanced branch filtering using direct branch name matching
    if branch:
        # Create flexible branch matching patterns
        branch_patterns = []
        
        # Common branch abbreviations to full names mapping
        branch_mappings = {
            'CS': ['Computer Science', 'Computer Science and Engineering'],
            'IT': ['Information Technology'],
            'ECE': ['Electronics and Communication', 'Electronics and Telecommunication'],
            'ENTC': ['Electronics and Telecommunication', 'Electronics and Communication'],
            'MECH': ['Mechanical Engineering', 'Mechanical'],
            'CIVIL': ['Civil Engineering', 'Civil'],
            'EEE': ['Electrical Engineering', 'Electrical and Electronics'],
            'ELECTRICAL': ['Electrical Engineering', 'Electrical and Electronics'],
            'CHEMICAL': ['Chemical Engineering', 'Chemical'],
            'BIOTECH': ['Biotechnology', 'Biomedical Engineering'],
            'AUTOMOBILE': ['Automobile Engineering', 'Automotive'],
            'PRODUCTION': ['Production Engineering', 'Manufacturing'],
            'INSTRUMENTATION': ['Instrumentation Engineering', 'Instrumentation']
        }
        
        # Add the original branch term
        branch_patterns.append(Cutoff.branch.ilike(f"%{branch}%"))
        
        # Check if the branch matches any known abbreviations
        branch_upper = branch.upper()
        if branch_upper in branch_mappings:
            for full_name in branch_mappings[branch_upper]:
                branch_patterns.append(Cutoff.branch.ilike(f"%{full_name}%"))
        
        # Apply OR condition for all branch patterns
        query = query.filter(or_(*branch_patterns))
    
    # Apply the same category and seat type filters as main function
    caste = caste.upper().strip()
    gender = gender.upper().strip()
    seat_type = seat_type.upper().strip()
    
    seat_type_mapping = {
        "H": "home",
        "O": "other", 
        "S": "state",
        "AI": "all india"
    }
    
    if seat_type in seat_type_mapping:
        query = query.filter(Cutoff.level.contains(seat_type_mapping[seat_type]))
    
    # Use the same category pattern logic as get_suggested_colleges
    gender_code = 'G' if gender == 'MALE' else 'L'
    seat_type_code_mapping = {
        "H": "H",
        "O": "O", 
        "S": "S",
        "AI": "AI"
    }
    seat_type_code = seat_type_code_mapping.get(seat_type, "S")
    
    # Handle special reservations
    if special_reservation:
        special_code = special_reservation.upper()
        if special_code == 'PWD':
            category_patterns = [
                f"PWD{caste}{seat_type_code}",
                f"PWDR{caste}{seat_type_code}"
            ]
        elif special_code == 'DEFENCE':
            category_patterns = [
                f"DEFR{caste}{seat_type_code}",
                f"DEF{caste}{seat_type_code}"
            ]
        elif special_code == 'ORPHAN':
            category_patterns = [f"ORPHAN"]
        elif special_code == 'TFWS':
            category_patterns = [f"TFWS"]
        else:
            category_patterns = [f"{special_code}{caste}{seat_type_code}"]
    else:
        category_patterns = [f"{gender_code}{caste}{seat_type_code}"]
    
    # Apply category filter
    category_filters = []
    for pattern in category_patterns:
        category_filters.append(Cutoff.category.like(f"%{pattern}%"))
    
    if category_filters:
        query = query.filter(or_(*category_filters))
    
    return query.order_by(Cutoff.rank.asc()).limit(limit).all()


def get_college_statistics(
    db: Session,
    rank: int,
    caste: str,
    gender: str,
    seat_type: str
) -> dict:
    """
    Get statistics about available colleges for the given student profile.
    
    Returns:
        Dictionary containing statistics like total colleges, branches, etc.
    """
    
    colleges = get_suggested_colleges(db, rank, caste, gender, seat_type, limit=1000)
    
    if not colleges:
        return {
            "total_colleges": 0,
            "total_branches": 0,
            "unique_colleges": 0,
            "seat_types": [],
            "categories": []
        }
    
    unique_colleges = set(college.college.name for college in colleges)
    unique_branches = set(college.branch for college in colleges)
    seat_types = set(college.level for college in colleges)
    categories = set(college.category for college in colleges)
    
    return {
        "total_colleges": len(colleges),
        "total_branches": len(unique_branches),
        "unique_colleges": len(unique_colleges),
        "seat_types": list(seat_types),
        "categories": list(categories),
        "rank_range": {
            "min": min(college.rank for college in colleges),
            "max": max(college.rank for college in colleges)
        }
    }
