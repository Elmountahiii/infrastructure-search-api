from datetime import date
from pathlib import Path

from fastapi import FastAPI, Query

from app.extractors.html import extract_html
from app.extractors.pdf import extract_pdf_pages
from app.models.document import DocumentCreate
from app.models.search import SearchResult
from app.services.search import search_documents


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


@app.get(
    "/search",
    response_model=list[SearchResult],
)
def search(
    q: str = Query(min_length=1),
    category: str | None = None,
    region: str | None = None,
    source: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(default=20, ge=1, le=100),
) -> list[SearchResult]:
    return search_documents(
        query=q,
        category=category,
        region=region,
        source=source,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
