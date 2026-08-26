from datetime import date
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from pydantic import HttpUrl

from app.extractors.html import extract_html
from app.extractors.pdf import extract_pdf_pages
from app.models.document import DocumentCreate
from app.models.ingestion import IngestionResult
from app.models.search import SearchResult
from app.services.content_hashing import calculate_content_hash
from app.services.document_extraction import extract_document
from app.services.document_storage import DuplicateDocumentError, save_document
from app.services.search import search_documents
from app.services.sectioning import split_into_sections


app = FastAPI(
    title="Infrastructure Search API",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post(
    "/documents",
    response_model=IngestionResult,
    status_code=201,
)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    source: str = Form(...),
    url: HttpUrl | None = Form(None),
    category: str = Form(...),
    region: str = Form(...),
    publication_date: date | None = Form(None),
) -> IngestionResult:
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    file_type = Path(file.filename).suffix.lower().lstrip(".")

    supported_types = {
        "txt",
        "md",
        "markdown",
        "html",
        "htm",
        "pdf",
    }

    if file_type not in supported_types:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {file_type}",
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty",
        )

    document = DocumentCreate(
        title=title,
        source=source,
        url=url,
        category=category,
        region=region,
        publication_date=publication_date,
    )

    try:
        text = extract_document(
            content=content,
            file_type=file_type,
        )

        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Document contains no extractable text",
            )

        content_hash = calculate_content_hash(text)

        sections = split_into_sections(text)

        document_id = save_document(
            document=document,
            file_type=file_type,
            content_hash=content_hash,
            sections=sections,
        )

    except DuplicateDocumentError as exc:
        raise HTTPException(
            status_code=409,
            detail=(
                "Document already exists "
                f"with id {exc.document_id}"
            ),
        ) from exc

    return IngestionResult(
        document_id=document_id,
        status="indexed",
        sections_indexed=len(sections),
    )

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
