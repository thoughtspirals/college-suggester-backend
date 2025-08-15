from app.database import SessionLocal
from app.utils.pdf_parser import load_college_data
import pdfplumber
import unicodedata

def extract_lines(pdf_path):
    lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            print(f"Extracting text from page {page_num}...")
            text = page.extract_text()
            if text:
                lines.extend(text.splitlines())
    return lines


def main():
    db = SessionLocal()
    try:
        pdf_lines = extract_lines("app/data/mh-cet-cap-1.pdf")  # Adjust path if needed
        load_college_data(pdf_lines, db)
    except Exception as e:
        print("❌ Error occurred:", e)
    finally:
        db.close()

if __name__ == "__main__":
    main()
