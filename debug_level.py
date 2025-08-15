import sys
sys.path.append('.')
from app.database import SessionLocal
from app.models import Cutoff
from sqlalchemy import distinct

db = SessionLocal()

# Check what level values exist for GOPENH category
levels = db.query(distinct(Cutoff.level)).filter(
    Cutoff.category == 'GOPENH'
).all()

print('Levels for GOPENH category:')
for level in levels:
    print(f'  "{level[0]}"')

# Check a sample record
sample = db.query(Cutoff).filter(Cutoff.category == 'GOPENH').first()
if sample:
    print(f'Sample GOPENH record:')
    print(f'  Category: {sample.category}')
    print(f'  Level: "{sample.level}"')
    print(f'  Rank: {sample.rank}')

# Check what happens if we remove level filter completely
print('\nTesting without level filter:')
from app.models import College
from sqlalchemy import or_

no_level_results = db.query(Cutoff).join(College).filter(
    Cutoff.rank >= 10000,
    Cutoff.rank.isnot(None),
    or_(
        Cutoff.category.like('%GOPENH%'),
        Cutoff.category.like('%GOPEN%')
    )
).limit(3).all()

print(f'Results without level filter: {len(no_level_results)}')
for result in no_level_results:
    print(f'  {result.college.name} - {result.branch} - {result.category} - Level: "{result.level}"')

db.close()
