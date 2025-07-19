# load_pdf_data.py
from app.database import SessionLocal, engine
from app.utils.pdf_parser import extract_cutoffs_from_pdf

# Path to your stored PDF file
pdf_path = "app/data/_final.pdf"

# Create a DB session
db = SessionLocal()

# Extract and insert cutoffs
extract_cutoffs_from_pdf(pdf_path, db)

# Close session
db.close()
