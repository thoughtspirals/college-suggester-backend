import re
import pdfplumber
import unicodedata
from sqlalchemy.orm import Session
from app.models import Cutoff, College
from app.database import engine
from datetime import datetime 


# Regular expressions
PAIR_PATTERN = re.compile(r"(\d+)\s*\(([\d.]+)\)")
COURSE_LINE_PATTERN = re.compile(r"^\d{9} -")
CATEGORY_LINE_PATTERN = re.compile(r"^[A-Z0-9]+(?:\s+[A-Z0-9]+)+$")
RANK_LINE_PATTERN = re.compile(r"^(\d+\s+)+\d+$")
PERCENT_PATTERN = re.compile(r"\(([\d.]+)\)")

# Keyword filters
SKIP_KEYWORDS = ["Polytechnic", "Diploma", "ITI", "MSBTE"]
VALID_KEYWORDS = ["College", "Institute", "Engineering", "Technology"]

# Helper functions
def is_course_line(line: str) -> bool:
    return COURSE_LINE_PATTERN.match(line) is not None

def looks_like_college_code(line: str) -> bool:
    return re.match(r"^\d{9}[A-Z]?\s+-", line) is not None

def is_valid_college_line(line: str) -> bool:
    line_lower = line.lower()
    skip_lower = [w.lower() for w in SKIP_KEYWORDS]
    valid_lower = [w.lower() for w in VALID_KEYWORDS]

    return (
        " - " in line and
        not any(word in line_lower for word in skip_lower) and
        any(word in line_lower for word in valid_lower) and
        not is_course_line(line) and
        not looks_like_college_code(line)
    )


# Main extraction logic
def extract_cutoffs_from_pdf(file_path: str, db: Session):
    with pdfplumber.open(file_path) as pdf:
        college = branch = None
        current_category_line = ""
        rank_line = None
        stage_marker = ""

        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")
            for line in lines:
                line = unicodedata.normalize("NFKC", line.strip())
                print(f"🔍 Raw line: '{line}'")

                if is_valid_college_line(line):
                    college = line
                    print(f"\n🏫 Detected College: {college}")
                    continue

                if is_course_line(line):
                    branch = line.split(" - ", 1)[1].strip()
                    print(f"📘 Detected Branch: {branch}")
                    continue

                if "Stage-I" in line or "Stage-II" in line:
                    stage_marker = line
                    print(f"🧭 Stage Marker: {stage_marker}")
                    continue

                if CATEGORY_LINE_PATTERN.match(line) and not all(word.isdigit() for word in line.split()):
                    current_category_line = line
                    print(f"📋 Category Line Detected: {current_category_line}")
                    continue

                if RANK_LINE_PATTERN.match(line):
                    rank_line = list(map(int, line.split()))
                    print(f"📈 Rank Line: {rank_line}")
                    continue

                percent_matches = PERCENT_PATTERN.findall(line)
                if percent_matches and rank_line:
                    
                    # if "Stage-II" in stage_marker:
                    #     print("⏩ Skipping Stage-II block")
                    #     rank_line = None
                    #     continue

                    percents = list(map(float, percent_matches))
                    categories = current_category_line.split()

                    print(f"🔎 Current Category Line: {current_category_line}")
                    print(f"🧠 Parsed Categories: {categories}")
                    print(f"📊 Parsed Percents: {percents}")
                    print(f"🔢 Count -> Categories: {len(categories)}, Ranks: {len(rank_line)}, Percents: {len(percents)}")

                    for i, cat in enumerate(categories):
                        rank = rank_line[i] if i < len(rank_line) else None
                        percent = percents[i] if i < len(percents) else None

                        gender = "female" if "L" in cat else "male"
                        level = (
                            "state" if "S" in cat
                            else "other" if "O" in cat
                            else "home"
                        )

                        if college and branch:
                            cutoff = Cutoff(
                            college=college,
                            branch=branch,
                            category=cat,
                            rank=rank,
                            percent=percent,
                            gender=gender,
                            level=level,
                            stage=stage_marker.strip(),         
                            year=datetime.now().year-1              
                        )
                            db.add(cutoff)
                            print(f"✅ Page {page_num}: Added -> {cat} | Rank: {rank} | Percent: {percent}")
                        else:
                            print(f"⚠️ Skipped due to missing college/branch for {cat}")

                    rank_line = None  # Reset

        print("🔍 Final Record Count Before Commit:", len(db.new))
        db.commit()
        print(f"📦 Committed to DB at: {engine.url}")
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

