from pathlib import Path

from fastapi import FastAPI

from app.extractors.html import extract_html
from app.extractors.pdf import extract_pdf_pages
from app.models.document import DocumentCreate


app = FastAPI(
    title="Infrastructure Search API",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/document")
def create_document(document:DocumentCreate):
  # content = Path("samples/ties-one-year-on-annex.pdf").read_bytes()
  # pages = extract_pdf_pages(content)
  # print(f"Pages: {len(pages)}")
  return document
