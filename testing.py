

from pathlib import Path

from app.extractors.pdf import extract_pdf_pages
from app.services.pdf_cleaning import remove_repeated_headers_footers
from app.services.text_cleaning import clean_text


PROJECT_ROOT = Path(__file__).parent


def main() -> None:
    content = (PROJECT_ROOT / "samples" / "ties-one-year-on-annex.pdf").read_bytes()
    pages = extract_pdf_pages(content)
    pages = [clean_text(page) for page in pages]

    cleaned_pages = remove_repeated_headers_footers(pages)
    for index,page in enumerate(pages):
      print(f"----- {index}-----\n  {clean_text(page)}")




if __name__ == "__main__":
    main()
