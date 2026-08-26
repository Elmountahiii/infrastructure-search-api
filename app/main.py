import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import HttpUrl

from app.db.connection import initialize_database
from app.extractors.html import extract_html
from app.extractors.pdf import extract_pdf_pages
from app.logging_config import configure_logging
from app.models.document import DocumentCreate, DocumentDetail, DocumentSummary
from app.models.ingestion import IngestionResult
from app.models.search import SearchResult
from app.models.stats import StatsResponse
from app.services.content_hashing import calculate_content_hash
from app.services.document_extraction import DocumentExtractionError, extract_document
from app.services.document_storage import (
    DuplicateDocumentError,
    get_document,
    get_documents,
    save_document,
)
from app.services.search import InvalidSearchQueryError, search_documents
from app.services.sectioning import split_into_sections
from app.services.stats import get_stats


configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    initialize_database()
    yield


def _truncate_for_log(value: str, limit: int = 200) -> str:
    if len(value) <= limit:
        return value

    return f"{value[:limit - 3]}..."


app = FastAPI(
    title="Infrastructure Search API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def handle_unexpected_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.error(
        "event=unhandled_request_error method=%s path=%r error=%s",
        request.method,
        request.url.path,
        type(exc).__name__,
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Welcome to the Infrastructure Search API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/stats",
    response_model=StatsResponse,
)
def stats() -> StatsResponse:
    return get_stats()


@app.get(
    "/documents",
    response_model=list[DocumentSummary],
)
def list_documents() -> list[DocumentSummary]:
    return get_documents()


@app.get(
    "/documents/{document_id}",
    response_model=DocumentDetail,
)
def retrieve_document(document_id: int) -> DocumentDetail:
    document = get_document(document_id)

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return document


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
    start = perf_counter()
    filename = file.filename or ""
    file_type = Path(filename).suffix.lower().lstrip(".")
    logged_filename = _truncate_for_log(filename)

    logger.info(
        "event=document_ingestion_started filename=%r file_type=%s",
        logged_filename,
        file_type or "none",
    )

    try:
        if not filename:
            raise HTTPException(
                status_code=400,
                detail="Filename is required",
            )

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

        text = extract_document(
            content=content,
            file_type=file_type,
        )

        characters_processed = len(text)

        logger.info(
            "event=document_extraction_completed "
            "filename=%r file_type=%s characters_processed=%d "
            "processing_ms=%.2f",
            logged_filename,
            file_type,
            characters_processed,
            (perf_counter() - start) * 1000,
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
        logger.warning(
            "event=duplicate_document_detected "
            "filename=%r file_type=%s document_id=%d processing_ms=%.2f",
            logged_filename,
            file_type or "none",
            exc.document_id,
            (perf_counter() - start) * 1000,
        )

        raise HTTPException(
            status_code=409,
            detail=(
                "Document already exists "
                f"with id {exc.document_id}"
            ),
        ) from exc

    except DocumentExtractionError as exc:
        cause = exc.__cause__ or exc

        logger.warning(
            "event=document_ingestion_failed "
            "filename=%r file_type=%s error=%s status_code=400 "
            "processing_ms=%.2f",
            logged_filename,
            file_type or "none",
            type(cause).__name__,
            (perf_counter() - start) * 1000,
        )

        raise HTTPException(
            status_code=400,
            detail="Document could not be extracted",
        ) from exc

    except HTTPException as exc:
        logger.warning(
            "event=document_ingestion_failed "
            "filename=%r file_type=%s error=http_error status_code=%d "
            "processing_ms=%.2f",
            logged_filename,
            file_type or "none",
            exc.status_code,
            (perf_counter() - start) * 1000,
        )
        raise

    except Exception as exc:
        logger.exception(
            "event=document_ingestion_failed "
            "filename=%r file_type=%s error=%s status_code=500 "
            "processing_ms=%.2f",
            logged_filename,
            file_type or "none",
            type(exc).__name__,
            (perf_counter() - start) * 1000,
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        ) from exc

    processing_ms = (perf_counter() - start) * 1000

    logger.info(
        "event=document_indexed document_id=%d filename=%r file_type=%s "
        "sections_count=%d characters_processed=%d processing_ms=%.2f",
        document_id,
        logged_filename,
        file_type,
        len(sections),
        characters_processed,
        processing_ms,
    )

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
    start = perf_counter()
    logged_query = _truncate_for_log(q)

    try:
        results = search_documents(
            query=q,
            category=category,
            region=region,
            source=source,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )

    except InvalidSearchQueryError as exc:
        logger.warning(
            "event=search_failed query=%r error=invalid_search_query "
            "status_code=400 processing_ms=%.2f",
            logged_query,
            (perf_counter() - start) * 1000,
        )

        raise HTTPException(
            status_code=400,
            detail="Invalid search query",
        ) from exc

    except Exception as exc:
        logger.exception(
            "event=search_failed query=%r error=%s status_code=500 "
            "processing_ms=%.2f",
            logged_query,
            type(exc).__name__,
            (perf_counter() - start) * 1000,
        )

        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        ) from exc

    logger.info(
        "event=search_completed query=%r result_count=%d category=%r "
        "region=%r source=%r date_from=%s date_to=%s processing_ms=%.2f",
        logged_query,
        len(results),
        category,
        region,
        source,
        date_from.isoformat() if date_from else None,
        date_to.isoformat() if date_to else None,
        (perf_counter() - start) * 1000,
    )

    return results
