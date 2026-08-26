from pathlib import Path

from app.db.connection import initialize_database
from app.extractors.pdf import extract_pdf_pages
from app.services.content_hashing import calculate_content_hash
from app.services.document_extraction import extract_document
from app.services.pdf_cleaning import remove_repeated_headers_footers
from app.services.sectioning import split_into_sections
from app.services.text_cleaning import clean_text


PROJECT_ROOT = Path(__file__).parent


def main() -> None:
    initialize_database()
    content = (PROJECT_ROOT / "samples" / "water-network.md").read_bytes()
    text = extract_document(content=content,file_type="md")
    sections = split_into_sections(text=text)
    # print("------ RAW TEXT -------")
    # print(text)
    # print("------------ END -------")
    print("------ SECTIONS -------")
    for section in sections:
      print(f"index: {section.order} :\ntitle: {section.title}:\ntext: {section.text}\n")


if __name__ == "__main__":
    main()
