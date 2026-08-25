

from pathlib import Path

from app.extractors.pdf import extract_pdf_pages
from app.services.text_cleaning import clean_text


PROJECT_ROOT = Path(__file__).parent


def main() -> None:
    content = (PROJECT_ROOT / "samples" / "ties-one-year-on-annex.pdf").read_bytes()
    pages = extract_pdf_pages(content)

    for index,page in enumerate(pages):
      print(f"----- {index}-----\n  {clean_text(page)}")



if __name__ == "__main__":
    main()
