from app.database import engine, Base
from app.models import Cutoff, College  # Make sure Cutoff is imported here

# Create all tables defined in Base's subclasses
Base.metadata.create_all(bind=engine)

print("✅ Tables created successfully.")

