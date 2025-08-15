#!/usr/bin/env python3
"""
Test script for the updated PDF parser
"""

import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.utils.pdf_parser import extract_cutoffs_from_pdf
from app.models import Cutoff, College

def test_parser_limited():
    """Test the parser with limited pages for verification"""
    db = SessionLocal()
    
    try:
        # First, let's see what colleges we have
        college_count = db.query(College).count()
        print(f"📊 Current colleges in database: {college_count}")
        
        # Check current cutoffs
        cutoff_count = db.query(Cutoff).count()
        print(f"📊 Current cutoffs in database: {cutoff_count}")
        
        print("\n🔍 Starting limited PDF parsing test...")
        print("Note: This will parse the entire PDF as the parser now handles the structure correctly")
        
        # Run the parser
        extract_cutoffs_from_pdf("app/data/mh-cet-cap-1.pdf", db)
        
        # Check final counts
        final_college_count = db.query(College).count()
        final_cutoff_count = db.query(Cutoff).count()
        
        print(f"\n📊 Final Results:")
        print(f"   Colleges: {final_college_count} (added: {final_college_count - college_count})")
        print(f"   Cutoffs: {final_cutoff_count} (added: {final_cutoff_count - cutoff_count})")
        
        # Show sample data
        print(f"\n📋 Sample cutoffs:")
        sample_cutoffs = db.query(Cutoff).limit(5).all()
        for cutoff in sample_cutoffs:
            print(f"   {cutoff.college.name} - {cutoff.branch} - {cutoff.category}: Rank {cutoff.rank}")
        
    except Exception as e:
        print(f"❌ Error during parsing: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_parser_limited()
