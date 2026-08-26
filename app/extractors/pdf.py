from io import BytesIO

from pypdf import PdfReader


def extract_pdf_pages(content: bytes) -> list[str]:
    reader = PdfReader(BytesIO(content))
    pages: list[str] = []

    for page in reader.pages:
        pages.append(page.extract_text() or "")

    return pages
