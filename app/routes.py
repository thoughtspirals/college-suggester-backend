from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    CollegeSuggestionRequest, 
    CollegeSuggestionResponse, 
    CollegeStatistics
)
from app.crud import get_top_colleges
from app.apis.college_suggestion import (
    get_suggested_colleges,
    get_college_details_by_rank,
    get_college_statistics
)
from typing import List, Optional

router = APIRouter()

# Updated endpoint using new get_suggested_colleges function
@router.get("/recommend", response_model=List[CollegeSuggestionResponse])
def recommend_colleges(
    rank: int = Query(..., description="Student's CET rank"),
    caste: str = Query(..., description="Student's caste category (OPEN, OBC, SC, ST, EWS, NT1, NT2, NT3, SBC, SEBC, VJ)"),
    gender: str = Query(..., description="Student's gender (MALE, FEMALE)"),
    seat_type: str = Query("H", description="Type of seat (H-Home, O-Other, S-State, AI-All India)"),
    special_reservation: Optional[str] = Query(None, description="Special reservation type (PWD, DEFENCE, ORPHAN, TFWS)"),
    limit: int = Query(20, description="Maximum number of colleges to return"),
    db: Session = Depends(get_db)
):
    """
    Get college recommendations based on student's rank and preferences.
    
    Updated to use the new get_suggested_colleges function with comprehensive filtering.
    Returns colleges where the student's rank is better than or equal to the cutoff rank,
    sorted by cutoff rank (lowest cutoff first).
    """
    try:
        colleges = get_suggested_colleges(
            db, rank, caste, gender, seat_type, special_reservation, limit
        )
        
        if not colleges:
            raise HTTPException(
                status_code=404, 
                detail="No colleges found for the given criteria"
            )
        
        # Convert to response format
        response = []
        for college in colleges:
            response.append(CollegeSuggestionResponse(
                college=college.college.name,  # Access college name through relationship
                branch=college.branch,
                category=college.category,
                rank=college.rank,
                percent=college.percent,
                gender=college.gender,
                level=college.level,
                year=college.year,
                stage=college.stage
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")




@router.get("/college-details", response_model=List[CollegeSuggestionResponse])
def get_college_details(
    rank: int = Query(..., description="Student's CET rank"),
    caste: str = Query(..., description="Student's caste category"),
    gender: str = Query(..., description="Student's gender"),
    seat_type: str = Query(..., description="Type of seat"),
    special_reservation: Optional[str] = Query(None, description="Special reservation type (PWD, DEFENCE, ORPHAN, TFWS)"),
    college_name: Optional[str] = Query(None, description="Specific college name"),
    branch: Optional[str] = Query(None, description="Specific branch name (can be normalized name like 'CS' or full name)"),
    db: Session = Depends(get_db)
):
    """
    Get detailed cutoff information for specific college/branch combination.
    Uses normalized branch names from ranked_colleges table for better search.
    """
    try:
        colleges = get_college_details_by_rank(
            db, rank, caste, gender, seat_type, college_name, branch, special_reservation
        )
        
        if not colleges:
            raise HTTPException(
                status_code=404, 
                detail="No colleges found for the given criteria"
            )
        
        # Convert to response format with normalized branch names
        response = []
        for college in colleges:
            # Get normalized branch name if available
            normalized_branch = college.branch
            if hasattr(college, 'normalized_branch') and college.normalized_branch:
                normalized_branch = college.normalized_branch
            
            response.append(CollegeSuggestionResponse(
                college=college.college.name,  # Access college name through relationship
                branch=normalized_branch,  # Use normalized branch name
                category=college.category,
                rank=college.rank,
                percent=college.percent,
                gender=college.gender,
                level=college.level,
                year=college.year,
                stage=college.stage
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/college-statistics", response_model=CollegeStatistics)
def get_statistics(
    rank: int = Query(..., description="Student's CET rank"),
    caste: str = Query(..., description="Student's caste category"),
    gender: str = Query(..., description="Student's gender"),
    seat_type: str = Query(..., description="Type of seat"),
    db: Session = Depends(get_db)
):
    """
    Get statistics about available colleges for the given student profile.
    """
    try:
        stats = get_college_statistics(db, rank, caste, gender, seat_type)
        return CollegeStatistics(**stats)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# POST endpoint for college suggestions
@router.post("/suggest-colleges", response_model=List[CollegeSuggestionResponse])
def suggest_colleges_post(
    request: CollegeSuggestionRequest,
    db: Session = Depends(get_db)
):
    """
    Get top colleges based on student's rank and preferences (POST version).
    
    Takes a JSON request body with student information and returns colleges
    where the student's rank is better than or equal to the cutoff rank,
    sorted by cutoff rank (lowest cutoff first).
    """
    try:
        colleges = get_suggested_colleges(
            db, 
            request.rank, 
            request.caste, 
            request.gender, 
            request.seat_type, 
            request.special_reservation,
            limit=20
        )
        
        if not colleges:
            raise HTTPException(
                status_code=404, 
                detail="No colleges found for the given criteria"
            )
        
        # Convert to response format
        response = []
        for college in colleges:
            response.append(CollegeSuggestionResponse(
                college=college.college.name,  # Access college name through relationship
                branch=college.branch,
                category=college.category,
                rank=college.rank,
                percent=college.percent,
                gender=college.gender,
                level=college.level,
                year=college.year,
                stage=college.stage
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/available-regions", response_model=List[str])
def get_available_regions(db: Session = Depends(get_db)):
    """
    Get all available regions for college filtering.
    Excludes unwanted entries and cleans up region names.
    """
    try:
        from app.models import College
        from sqlalchemy import distinct
        import re
        
        regions = db.query(distinct(College.region)).all()
        
        # Filter out None values and unwanted entries
        filtered_regions = []
        for r in regions:
            if r[0] and r[0].strip():
                region_name = r[0].strip()
                
                # Skip unwanted entries
                if any(unwanted in region_name for unwanted in [
                    "Atma Malik Institute Of Technology & Research",
                    "Ashokrao Mane Group of Institutions"
                ]):
                    continue
                
                # Clean up region names
                # Remove "Dist-" prefix (case insensitive)
                region_name = re.sub(r'^Dist[-\s]*', '', region_name, flags=re.IGNORECASE)
                # Remove "Tal-" prefix (case insensitive)
                region_name = re.sub(r'^Tal[-\s]*', '', region_name, flags=re.IGNORECASE)
                # Remove "Tal." prefix (case insensitive)
                region_name = re.sub(r'^Tal\.\s*', '', region_name, flags=re.IGNORECASE)
                # Remove "District" prefix (case insensitive)
                region_name = re.sub(r'^District\s+', '', region_name, flags=re.IGNORECASE)
                
                # Clean up extra spaces and punctuation
                region_name = region_name.strip()
                
                if region_name and region_name not in filtered_regions:
                    filtered_regions.append(region_name)
        
        # Sort and return unique regions
        available_regions = sorted(list(set(filtered_regions)))
        
        return available_regions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/available-branches", response_model=List[str])
def get_available_branches(db: Session = Depends(get_db)):
    """
    Get all unique branch names from the ranked_colleges table.
    Returns normalized branch names that can be used for filtering.
    """
    try:
        from app.models import RankedCollege
        from sqlalchemy import distinct
        
        # Query for distinct branch names from ranked_colleges table
        branches = db.query(distinct(RankedCollege.branch)).all()
        
        # Filter out None values and clean up branch names
        filtered_branches = []
        for b in branches:
            if b[0] and b[0].strip():
                branch_name = b[0].strip()
                
                # Skip empty or very short branch names
                if len(branch_name) < 2:
                    continue
                
                if branch_name not in filtered_branches:
                    filtered_branches.append(branch_name)
        
        # Sort and return unique branches
        available_branches = sorted(list(set(filtered_branches)))
        
        return available_branches
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
