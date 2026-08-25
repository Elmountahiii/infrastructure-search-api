from pathlib import Path

from fastapi import FastAPI

from app.extractors.html import extract_html
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
  # content = Path("samples/broadband-programme.html").read_bytes()
  # to_markdown = extract_html(content)
  # print(to_markdown)
  return document
