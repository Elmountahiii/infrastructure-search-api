from io import BytesIO

from pypdf import PdfReader

def extract_pdf_pages(content: bytes):
  reader = PdfReader(BytesIO(content))
  pages:list[str] = []
  for page in reader.pages:
    text = page.extract_text()
    pages.append(text)

  return pages
