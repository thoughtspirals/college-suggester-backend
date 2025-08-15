import sys
sys.path.append('.')
from app.database import SessionLocal
from app.apis.college_suggestion import get_suggested_colleges

db = SessionLocal()

try:
    # Test with rank 10000 and seat_type H (should now map to "other" level)
    colleges = get_suggested_colleges(
        db, 
        rank=10000, 
        caste='OPEN', 
        gender='MALE', 
        seat_type='H', 
        special_reservation=None, 
        limit=5
    )
    
    print(f'Found {len(colleges)} colleges for rank 10000, MALE, OPEN, Home seat')
    
    if colleges:
        for i, college in enumerate(colleges[:5]):
            print(f'{i+1}. {college.college.name}')
            print(f'   Branch: {college.branch}')
            print(f'   Category: {college.category}')
            print(f'   Rank: {college.rank}')
            print(f'   Level: {college.level}')
            print()
    else:
        print('Still no results!')
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()

db.close()
