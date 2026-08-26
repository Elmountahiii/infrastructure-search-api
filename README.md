# Infrastructure Search API

## Overview

Infrastructure Search API is a fictional Regional Infrastructure Intelligence technical assessment. It ingests public or fictional infrastructure documents, extracts and cleans their text, divides the content into searchable sections, and provides structured lexical search through a REST API.

The service accepts PDF, HTML, Markdown, and TXT files. It is intentionally a small, self-contained local demonstration rather than a production document platform.

A live hosted version is available at
[https://infrastructure-api.elmountahi.dev/](https://infrastructure-api.elmountahi.dev/).
Interactive API documentation is available at
[https://infrastructure-api.elmountahi.dev/docs](https://infrastructure-api.elmountahi.dev/docs).

## Features

- Multi-format document ingestion through `multipart/form-data`
- PDF, HTML, Markdown, and UTF-8 text extraction
- Unicode normalization and whitespace cleaning
- Heuristic repeated PDF header and footer removal
- Heading-aware sectioning with paragraph-based size splitting
- Explicit document metadata and optional publication dates
- SHA-256 duplicate detection based on normalized content
- SQLite persistence with SQLite FTS5 indexing
- FTS5 `MATCH` queries, BM25 relevance ordering, and highlighted snippets
- Category, region, source, and publication-date filters
- Document listing, document detail, and aggregate index statistics
- Structured console logging and consistent HTTP error handling
- Pytest coverage and a single-container Docker setup

## Architecture

```text
uploaded file
    |
    v
format-specific extraction
    |
    v
text and PDF-edge cleaning
    |
    v
SHA-256 content hash
    |
    v
structural sectioning
    |
    v
SQLite documents + sections
    |
    v
SQLite FTS5 index
    |
    v
search API
```

A **document** stores ingestion metadata such as title, source, category, region, publication date, file type, and content hash. A **section** stores an ordered, searchable unit of extracted text belonging to a document. Search runs against section titles and section text, then joins each match back to its document metadata.

Database initialization is part of the FastAPI application lifespan. A first start creates the data directory, relational tables, FTS5 table, and synchronization triggers automatically; no manual schema command is required.

## Technology Choices

### FastAPI

FastAPI provides a small REST layer, Pydantic request and response validation, generated OpenAPI metadata, and an interactive Swagger UI.

### SQLite

SQLite keeps evaluator setup self-contained and is appropriate for the expected demonstration-scale workload. The database is a local file at `data/infrastructure.db`; no separate database service is required.

### SQLite FTS5

FTS5 supplies lexical `MATCH` queries, BM25 ranking, and snippets without introducing Elasticsearch or another search service. This keeps the architecture easy to run and inspect, at the cost of distributed scaling and semantic search capabilities.

### uv

uv manages the Python environment and dependencies. The committed `uv.lock` enables reproducible installs with `uv sync --frozen`, including inside the Docker image.

## Requirements

For local development:

- Python 3.12
- [uv](https://docs.astral.sh/uv/)

For the containerized setup:

- Docker
- Docker Compose v2 (`docker compose`)

## Local Development Setup

From a clean clone:

```bash
uv sync
uv run fastapi dev app/main.py
```

Open Swagger UI at <http://localhost:8000/docs>. The application creates `data/infrastructure.db` on startup.

## Docker Setup

Build and start the API with:

```bash
docker compose up --build
```

Then open <http://localhost:8000/docs>.

Compose runs one FastAPI container and maps host port 8000 to container port 8000. A named volume, `infrastructure_data`, is mounted at `/app/data`, so `/app/data/infrastructure.db` survives container recreation.

When the container starts, it waits for the API health endpoint and then runs
`scripts/ingest_samples.py`. Existing sample documents are skipped through the
API's duplicate detection, so restarting the container does not create copies.

Stop the service while retaining indexed data:

```bash
docker compose down
```

To reset the Docker database completely, also delete the named volume:

```bash
docker compose down --volumes
```

## API

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | Return a welcome message and useful API links. |
| `GET` | `/health` | Return service health. |
| `POST` | `/documents` | Extract, section, and index one uploaded document. |
| `GET` | `/documents` | List indexed documents with their section counts. |
| `GET` | `/documents/{id}` | Return one document and its ordered sections. |
| `GET` | `/search` | Search indexed sections with optional metadata and date filters. |
| `GET` | `/stats` | Return current index totals and document breakdowns. |

The generated Swagger UI provides the complete request and response schemas.

## Document Ingestion

`POST /documents` accepts `multipart/form-data` with these fields:

| Field | Required | Description |
| --- | --- | --- |
| `file` | Yes | A `.pdf`, `.html`, `.htm`, `.md`, `.markdown`, or `.txt` file. |
| `title` | Yes | Human-readable document title. |
| `source` | Yes | Publisher or source organization. |
| `url` | No | Valid source URL. |
| `category` | Yes | Caller-supplied category, such as `transport`. |
| `region` | Yes | Caller-supplied geographic region. |
| `publication_date` | No | Publication date in `YYYY-MM-DD` format. |

Example:

```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@samples/rail-report.txt;type=text/plain" \
  -F "title=Regional Rail Development Report" \
  -F "source=Regional Infrastructure Authority" \
  -F "url=https://example.org/reports/rail-development" \
  -F "category=transport" \
  -F "region=Bavaria" \
  -F "publication_date=2025-04-10"
```

A successful ingestion returns `201 Created` with the document ID and number of indexed sections. Important ingestion errors include:

- `409 Conflict` when the normalized content already exists
- `415 Unsupported Media Type` for an unsupported filename extension
- `400 Bad Request` for an empty upload, text with no extractable content, or extraction failure
- `422 Unprocessable Entity` for missing or invalid form fields

File support is determined from the uploaded filename extension, not its MIME type.

## Search

Examples:

```text
GET /search?q=bridge
GET /search?q=bridge&region=Bavaria
GET /search?q=solar&category=energy
GET /search?q=grid&date_from=2024-01-01&date_to=2026-01-01
```

`q` is passed to SQLite FTS5 as a `MATCH` expression. Results are section-level matches ordered by ascending FTS5 BM25 value; the API exposes the negated value as `score`, so stronger matches generally have higher returned scores.

Each result includes document metadata, the matched section ID/title, and a compact snippet. Matching terms use square-bracket markers, for example `[bridge]`. Search defaults to 20 results and accepts a `limit` from 1 to 100. Malformed FTS5 expressions return `400 Bad Request`.

### Filtering

Search supports exact-match document metadata filters:

- `category`
- `region`
- `source`
- `date_from` (inclusive)
- `date_to` (inclusive)

FTS5 matches section titles and text, while filters apply to the owning document. Publication dates are stored as ISO dates, which makes the inclusive string comparisons chronologically valid.

## Extraction

### TXT

TXT files are decoded as UTF-8, with an optional UTF-8 byte-order mark removed.

### Markdown

Markdown is decoded as UTF-8 and keeps its source heading markers. ATX headings (`#` through `######`) become section boundaries.

### HTML

BeautifulSoup parses the document. `script`, `style`, `noscript`, and `nav` elements are removed, and HTML heading elements are converted to Markdown-style headings before the visible text is collected.

### PDF

pypdf extracts text page by page. Each page is cleaned before repeated edge lines are removed, then the pages are joined and cleaned again. This supports text-based PDFs; it does not perform OCR.

All extracted formats receive NFKC Unicode normalization, newline normalization, horizontal-whitespace collapsing, line trimming, and repeated-empty-line collapsing.

## PDF Header/Footer Removal

The PDF cleaner uses an intentionally understandable heuristic:

1. Inspect candidate lines near the top and bottom of every page (three lines by default).
2. Lowercase and normalize whitespace in candidates.
3. Replace digit sequences with `#`, allowing `Page 1`, `Page 2`, and similar lines to match.
4. Treat candidates appearing on at least 60% of pages as probable repeated headers or footers.
5. Remove matching text only from page-edge positions, preserving the same phrase when it occurs in body content.

This works for common report furniture but is not a general PDF layout engine.

## Sectioning

The sectioner prefers explicit headings. Markdown headings—and HTML headings converted during extraction—start new sections while their following paragraphs remain together. Sections larger than the default target of approximately 3,000 characters are split at paragraph boundaries.

TXT and PDF content without recognized `#` headings falls back to paragraph/size-based chunks. A single paragraph longer than the target is kept intact rather than cut in the middle.

## Duplicate Detection

Duplicate identity is based on content rather than filenames:

```text
extract -> normalize and clean -> SHA-256 -> compare content_hash
```

The application checks for an existing hash before insertion, and `documents.content_hash` also has a database `UNIQUE` constraint. Uploading the same normalized content under a different filename or with different metadata still returns `409 Conflict` and preserves the first document.

## Database Design

- `documents` stores metadata, file type, unique content hash, and creation time.
- `sections` stores ordered text units with a foreign key to `documents`.
- `sections_fts` is an external-content FTS5 table indexing `section_title` and `text`.

`sections.id` is used as `sections_fts.rowid`. Insert and delete triggers keep the FTS table synchronized with section creation and deletion. The current ingestion flow treats sections as immutable after creation, so no section update endpoint is exposed.

## Statistics

`GET /stats` calculates current database state and returns:

- `documents_indexed`
- `sections_indexed`
- `characters_indexed` (sum of stored section-text lengths)
- `documents_by_file_type`
- `documents_by_category`
- `documents_by_region`

These are live index totals. Processing failures and skipped duplicate attempts are logged but are not persisted as cumulative statistics.

## Logging and Error Handling

The application writes structured key-value-style events to standard output. Logged lifecycle events include ingestion start, extraction completion, successful indexing, duplicate detection, search completion, and failures, with useful fields such as file type, result count, processing time, and status code.

Expected client errors use explicit HTTP statuses. Unexpected exceptions are logged with stack traces while the API returns a generic `500 Internal Server Error` response rather than exposing internals.

## Tests

Run the test suite with:

```bash
uv run pytest
```

The current suite contains 25 tests covering API flows, extraction, text and PDF cleaning, sectioning, storage and duplicate handling, FTS5 search/ranking/filtering, document retrieval, statistics, and error responses. Each test receives a fresh temporary SQLite database initialized from the production schema.

## Sample Documents

The repository currently includes a small `samples/` directory with four development documents spanning the supported formats. Docker ingests these documents automatically at container startup through `scripts/ingest_samples.py`. It is not yet the planned assessment corpus of at least ten public/freely reusable or fictional infrastructure documents.

## Assumptions and Limitations

- Designed for a local technical demonstration, not high-scale or distributed production use
- Lexical FTS5 search only; no embeddings, vector database, semantic retrieval, RAG, or LLM features
- Text-based PDFs are supported; scanned/image-only PDFs require out-of-scope OCR
- Complex layouts and multi-column PDF reading order may extract imperfectly
- PDF semantic heading detection is weaker than Markdown and HTML heading detection
- No authentication, authorization, frontend, or batch ingestion endpoint
- No document-list pagination and no search offset pagination
- Category and region are supplied during ingestion rather than inferred
- Ingestion and extraction are synchronous, so very large files can occupy an API worker

## Design Trade-offs

- **SQLite/FTS5 instead of Elasticsearch:** removes external infrastructure and makes evaluation simple, while limiting horizontal scale and advanced search features.
- **Explicit metadata instead of inference:** keeps behavior deterministic and inspectable, while relying on callers to provide consistent categories and regions.
- **Heuristic PDF cleanup:** handles recurring report headers and numbered footers with little complexity, but cannot model every layout.
- **Structural sections before size splitting:** preserves meaningful document boundaries where headings exist, then controls chunk size at paragraph boundaries.
- **Application duplicate check plus database constraint:** provides a useful conflict message while retaining database-level integrity under concurrent attempts.
- **Synchronous ingestion:** is straightforward for the assessment workload, but long-running production extraction would benefit from limits or background processing.

## Future Improvements

- Add OCR for scanned PDFs
- Improve PDF layout and heading detection
- Add document and search pagination
- Complete the curated ten-document sample corpus
- Persist richer ingestion metrics such as failures and duplicate attempts
- Define a stronger category and region taxonomy
