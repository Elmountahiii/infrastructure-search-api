from pathlib import Path

from app.extractors.pdf import extract_pdf_pages
from app.services.document_extraction import extract_document
from app.services.pdf_cleaning import remove_repeated_headers_footers
from app.services.text_cleaning import clean_text


PROJECT_ROOT = Path(__file__).parent


def main() -> None:
    content = (PROJECT_ROOT / "samples" / "water-network.md").read_bytes()
    text = extract_document(content=content,file_type="md")
    print(text)

if __name__ == "__main__":
    main()
