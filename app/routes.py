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
from app.auth_dependencies import get_current_user, require_permission
from app.auth_utils import Permissions
from app.models import User
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
    current_user: User = Depends(require_permission(Permissions.READ_COLLEGES)),
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


@router.get("/branch-mappings")
def get_branch_mappings(db: Session = Depends(get_db)):
    """
    Get detailed branch information showing original names and their normalized versions.
    Useful for debugging and understanding the normalization process.
    """
    try:
        from app.models import RankedCollege, Cutoff
        from app.utils.branch_normalizer import BranchNormalizer
        from sqlalchemy import distinct
        
        normalizer = BranchNormalizer()
        
        # Collect branches from both tables
        all_branches = []
        
        # Get branches from cutoffs table
        try:
            cutoff_branches = db.query(distinct(Cutoff.branch)).all()
            for b in cutoff_branches:
                if b[0] and b[0].strip() and len(b[0].strip()) > 1:
                    all_branches.append(b[0].strip())
        except Exception as e:
            print(f"Warning: Could not fetch branches from cutoffs table: {e}")
        
        # Get branches from ranked_colleges table  
        try:
            ranked_branches = db.query(distinct(RankedCollege.branch)).all()
            for b in ranked_branches:
                if b[0] and b[0].strip() and len(b[0].strip()) > 1:
                    all_branches.append(b[0].strip())
        except Exception as e:
            print(f"Warning: Could not fetch branches from ranked_colleges table: {e}")
        
        # Remove duplicates
        unique_branches = list(set(all_branches))
        
        # Get mappings with original and normalized names
        branch_mappings = normalizer.get_all_branches_with_normalized(unique_branches)
        
        # Format response
        response = {
            "total_original_branches": len(unique_branches),
            "total_normalized_branches": len(set(mapping[1] for mapping in branch_mappings)),
            "mappings": [
                {
                    "original": original,
                    "normalized": normalized
                }
                for original, normalized in branch_mappings
            ]
        }
        
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
    limit: int = Query(50, description="Maximum number of results to return"),
    current_user: User = Depends(require_permission(Permissions.READ_COLLEGES)),
    db: Session = Depends(get_db)
):
    """
    Get detailed cutoff information for specific college/branch combination.
    Uses normalized branch names from ranked_colleges table for better search.
    """
    try:
        colleges = get_college_details_by_rank(
            db, rank, caste, gender, seat_type, college_name, branch, special_reservation, limit
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
    current_user: User = Depends(require_permission(Permissions.READ_COLLEGES)),
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
    current_user: User = Depends(require_permission(Permissions.READ_COLLEGES)),
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
    Get all unique branch names, collecting from both cutoffs and ranked_colleges tables.
    Returns normalized branch names (e.g., Computer Science -> CSE) for better consistency.
    """
    try:
        from app.models import RankedCollege, Cutoff
        from app.utils.branch_normalizer import BranchNormalizer
        from sqlalchemy import distinct, union
        
        normalizer = BranchNormalizer()
        
        # Collect branches from both tables
        all_branches = []
        
        # Get branches from cutoffs table
        try:
            cutoff_branches = db.query(distinct(Cutoff.branch)).all()
            for b in cutoff_branches:
                if b[0] and b[0].strip() and len(b[0].strip()) > 1:
                    all_branches.append(b[0].strip())
        except Exception as e:
            print(f"Warning: Could not fetch branches from cutoffs table: {e}")
        
        # Get branches from ranked_colleges table  
        try:
            ranked_branches = db.query(distinct(RankedCollege.branch)).all()
            for b in ranked_branches:
                if b[0] and b[0].strip() and len(b[0].strip()) > 1:
                    all_branches.append(b[0].strip())
        except Exception as e:
            print(f"Warning: Could not fetch branches from ranked_colleges table: {e}")
        
        # Remove duplicates
        unique_branches = list(set(all_branches))
        
        # Normalize all branches and get unique normalized names
        normalized_branches = normalizer.get_normalized_branches(unique_branches)
        
        return normalized_branches
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
