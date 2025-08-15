import re
import pdfplumber
import unicodedata
from sqlalchemy.orm import Session
from app.models import Cutoff, College
from app.database import engine
from datetime import datetime 


# Regular expressions
PAIR_PATTERN = re.compile(r"(\d+)\s*\(([\d.]+)\)")
# College pattern: 5 digits followed by dash and college name
COLLEGE_LINE_PATTERN = re.compile(r"^\d{5} - ")
# Course pattern: 10 digits followed by dash and course name
COURSE_LINE_PATTERN = re.compile(r"^\d{10} - ")
# Category line pattern: starts with "Stage" followed by categories
CATEGORY_LINE_PATTERN = re.compile(r"^Stage\s+[A-Z0-9]+(?:\s+[A-Z0-9]+)*$")
# Rank line pattern: starts with "I" followed by ranks
RANK_LINE_PATTERN = re.compile(r"^I\s+(\d+(?:\s+\d+)*)$")
# Percent pattern: parentheses with decimal numbers
PERCENT_PATTERN = re.compile(r"\(([\d.]+)\)")

# Keyword filters
SKIP_KEYWORDS = ["Polytechnic", "Diploma", "ITI", "MSBTE"]
VALID_KEYWORDS = ["College", "Institute", "Engineering", "Technology"]

# Helper functions
def is_college_line(line: str) -> bool:
    """Check if line matches college pattern: 01002 - Government College of Engineering, Amravati"""
    return COLLEGE_LINE_PATTERN.match(line) is not None

def is_course_line(line: str) -> bool:
    """Check if line matches course pattern: 0100219110 - Civil Engineering"""
    return COURSE_LINE_PATTERN.match(line) is not None

def is_category_line(line: str) -> bool:
    """Check if line matches category pattern: Stage GOPENS GSCS GSTS..."""
    return CATEGORY_LINE_PATTERN.match(line) is not None

def is_rank_line(line: str) -> bool:
    """Check if line matches rank pattern: I 34240 62739 91124..."""
    return RANK_LINE_PATTERN.match(line) is not None

def is_valid_college_line(line: str) -> bool:
    """Check if it's a valid college line (with proper keywords and not polytechnic/diploma)"""
    if not is_college_line(line):
        return False
    
    line_lower = line.lower()
    skip_lower = [w.lower() for w in SKIP_KEYWORDS]
    valid_lower = [w.lower() for w in VALID_KEYWORDS]

    return (
        not any(word in line_lower for word in skip_lower) and
        any(word in line_lower for word in valid_lower)
    )


def get_or_create_college(db: Session, college_line: str) -> College:
    """Extract college info and get or create college record"""
    # Parse college line: "01002 - Government College of Engineering, Amravati"
    match = re.match(r'^(\d{5}) - (.+)$', college_line)
    if not match:
        return None
        
    code = int(match.group(1))
    name = match.group(2).strip()
    
    # Try to find existing college
    college = db.query(College).filter(College.code == code, College.name == name).first()
    if college:
        return college
    
    # Create new college if not found
    college = College(
        code=code,
        name=name,
        status="Unknown",  # Will be updated when status info is available
        university="Unknown",
        region="Unknown"
    )
    db.add(college)
    db.flush()  # Get the ID without committing
    return college

# Main extraction logic
def extract_cutoffs_from_pdf(file_path: str, db: Session):
    with pdfplumber.open(file_path) as pdf:
        college_obj = branch = None
        college_line = ""
        current_category_line = ""
        rank_line = None
        stage_marker = "Stage-I"  # Default to Stage-I
        
        processed_count = 0
        skipped_count = 0

        for page_num, page in enumerate(pdf.pages, start=1):
            if page_num % 100 == 0:  # Progress indicator
                print(f"📄 Processing page {page_num}...")
                
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")
            for line_num, line in enumerate(lines):
                line = unicodedata.normalize("NFKC", line.strip())
                
                # Skip empty lines and header lines
                if not line or line.startswith('D Government') or line.startswith('i State Common') or line.startswith('r Cut Off List'):
                    continue

                # Detect college line
                if is_valid_college_line(line):
                    college_line = line
                    college_obj = get_or_create_college(db, college_line)
                    if college_obj:
                        print(f"\n🏫 Page {page_num}: Detected College: {college_line}")
                    continue

                # Detect course/branch line
                if is_course_line(line):
                    branch = line.split(" - ", 1)[1].strip()
                    print(f"📘 Page {page_num}: Detected Branch: {branch}")
                    continue
                
                # Detect stage markers (Stage-I, Stage-II in status or other indicators)
                if "Stage-I" in line or "Stage-II" in line:
                    stage_marker = "Stage-I" if "Stage-I" in line else "Stage-II"
                    print(f"🧭 Page {page_num}: Stage Marker: {stage_marker}")
                    continue

                # Detect category line (Stage GOPENS GSCS GSTS...)
                if is_category_line(line):
                    current_category_line = line
                    # Remove "Stage" from the beginning and get categories
                    categories = line.split()[1:]  # Skip "Stage" word
                    current_category_line = " ".join(categories)  # Store just categories
                    print(f"📋 Page {page_num}: Category Line: {current_category_line}")
                    continue

                # Detect rank line (I 34240 62739 91124...)
                if is_rank_line(line):
                    # Extract ranks after "I "
                    rank_numbers = line.split()[1:]  # Skip "I"
                    rank_line = [int(x) for x in rank_numbers]
                    print(f"📈 Page {page_num}: Rank Line: {rank_line}")
                    continue

                # Detect percentile line and process cutoffs
                percent_matches = PERCENT_PATTERN.findall(line)
                if percent_matches and rank_line and current_category_line:
                    
                    # Skip Stage-II processing if desired (uncomment next lines)
                    # if "Stage-II" in stage_marker:
                    #     print("⏩ Skipping Stage-II block")
                    #     rank_line = None
                    #     continue

                    percents = [float(x) for x in percent_matches]
                    categories = current_category_line.split()

                    print(f"\n🔍 Page {page_num}: Processing cutoff data")
                    print(f"📊 Categories ({len(categories)}): {categories}")
                    print(f"📈 Ranks ({len(rank_line)}): {rank_line[:5]}..." if len(rank_line) > 5 else f"📈 Ranks ({len(rank_line)}): {rank_line}")
                    print(f"📊 Percents ({len(percents)}): {percents[:5]}..." if len(percents) > 5 else f"📊 Percents ({len(percents)}): {percents}")

                    # Match categories with ranks and percents
                    for i, cat in enumerate(categories):
                        rank = rank_line[i] if i < len(rank_line) else None
                        percent = percents[i] if i < len(percents) else None

                        # Parse gender and level from category
                        gender = "female" if "L" in cat else "male"
                        if "S" in cat:
                            level = "state"
                        elif "O" in cat:
                            level = "other"
                        elif "H" in cat:
                            level = "home"
                        else:
                            level = "state"  # Default

                        if college_obj and branch and rank:
                            # Extract course code from the branch line if available
                            course_code = 0  # Default value
                            if hasattr(branch, 'split') and len(branch.split()) > 0:
                                # Try to extract course code from earlier processing
                                # For now, use a default value
                                course_code = 0
                            
                            cutoff = Cutoff(
                                college_id=college_obj.id,
                                college_code=college_obj.code,
                                branch=branch,
                                course_code=course_code,
                                category=cat,
                                rank=rank,
                                percent=percent,
                                gender=gender,
                                level=level,
                                stage=stage_marker,
                                year=2024  # Fixed year for MH-CET 2024-25
                            )
                            db.add(cutoff)
                            processed_count += 1
                            if processed_count % 100 == 0:
                                print(f"✅ Processed {processed_count} cutoffs so far...")
                        else:
                            skipped_count += 1
                            if college_obj is None:
                                print(f"⚠️ Page {page_num}: Skipped {cat} - missing college")
                            elif branch is None:
                                print(f"⚠️ Page {page_num}: Skipped {cat} - missing branch")
                            elif rank is None:
                                print(f"⚠️ Page {page_num}: Skipped {cat} - missing rank")

                    # Reset for next set
                    rank_line = None
                    
            # Commit periodically to avoid memory issues
            if page_num % 200 == 0:
                print(f"💾 Intermediate commit at page {page_num}...")
                db.commit()

        print(f"\n📊 Processing Summary:")
        print(f"✅ Successfully processed: {processed_count} cutoffs")
        print(f"⚠️ Skipped: {skipped_count} entries")
        print(f"🔍 Final Record Count Before Final Commit: {len(db.new)}")
        
        db.commit()
        print(f"📦 Final commit completed to DB: {engine.url}")
        print("✅ All cutoffs have been processed and saved.")

def extract_college_details(line):
    # Extract only code and name (without status)
    # Example: "1150 - Swavalambi Shikshan Sanstha's Sushganga Polytechnic, Wani"
    match = re.match(r"(\d+)\s*-\s*(.+)", line)
    if match:
        code = match.group(1).strip()
        name = match.group(2).strip()
        return code, name
    return None, None

def load_college_data(pdf_lines, db: Session):
    colleges_to_add = []
    seen_colleges = set()
    SKIP_KEYWORDS = ["Polytechnic", "Diploma", "ITI", "MSBTE", "architecture", "POLYTECHNIC"]

    i = 0
    while i < len(pdf_lines) - 2:
        code, name = extract_college_details(pdf_lines[i].strip())
        if code and name:
            # Skip college names with undesired keywords
            if any(keyword.lower() in name.lower() for keyword in SKIP_KEYWORDS):
                print(f"⛔ Skipped (Invalid Type): [{code}] {name}")
                i += 1
                continue

            status_line = pdf_lines[i + 2].strip()
            status_match = re.match(r"Status\s*:\s*(.+)", status_line, re.IGNORECASE)
            if status_match:
                status = status_match.group(1).strip()
                college_key = (code, name, status)
                if college_key not in seen_colleges:
                    colleges_to_add.append((code, name, status))
                    seen_colleges.add(college_key)
                    print(f"➕ Added College: [{code}] {name} ({status})")
                else:
                    print(f"⏩ Skipped Duplicate: [{code}] {name} ({status})")
                i += 3
                continue
        i += 1

    # Preview all collected colleges
    print("\n📋 Collected Colleges:")
    for idx, (code, name, status) in enumerate(colleges_to_add, 1):
        print(f"{idx}. [{code}] {name} ({status})")

    # Ask for confirmation
    confirm = input("\n✅ Commit this data to the database? (yes/no): ").strip().lower()
    if confirm in ('yes', 'y'):
        try:
            for code, name, status in colleges_to_add:
                college = College(code=code, name=name, status=status)
                db.add(college)
            db.commit()
            print("🎉 Data committed successfully.")
        except Exception as e:
            db.rollback()
            print("❌ Commit failed:", e)
    else:
        print("❌ Commit cancelled by user.")

