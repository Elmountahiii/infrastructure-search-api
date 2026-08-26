import pytest
from fastapi.testclient import TestClient


DOCUMENT_FORM = {
    "title": "Bridge report",
    "source": "Regional Authority",
    "category": "transport",
    "region": "Bavaria",
    "publication_date": "2025-04-10",
}


def _upload_text(client: TestClient, content: bytes = b"Bridge reinforcement programme"):
    return client.post(
        "/documents",
        data=DOCUMENT_FORM,
        files={"file": ("bridge-report.txt", content, "text/plain")},
    )


def test_root(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to the Infrastructure Search API",
        "docs": "/docs",
        "health": "/health",
    }


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ingestion_search_document_detail_and_stats(client: TestClient) -> None:
    upload = _upload_text(client)
    assert upload.status_code == 201
    ingestion = upload.json()
    assert ingestion["status"] == "indexed"
    assert ingestion["document_id"] > 0
    assert ingestion["sections_indexed"] == 1

    search = client.get("/search", params={"q": "reinforcement"})
    assert search.status_code == 200
    assert [result["document_id"] for result in search.json()] == [ingestion["document_id"]]

    detail = client.get(f"/documents/{ingestion['document_id']}")
    assert detail.status_code == 200
    assert detail.json()["title"] == "Bridge report"
    assert detail.json()["sections"][0]["text"] == "Bridge reinforcement programme"

    missing = client.get("/documents/999999")
    assert missing.status_code == 404

    stats = client.get("/stats")
    assert stats.status_code == 200
    assert stats.json() == {
        "documents_indexed": 1,
        "sections_indexed": 1,
        "characters_indexed": len("Bridge reinforcement programme"),
        "documents_by_file_type": {"txt": 1},
        "documents_by_category": {"transport": 1},
        "documents_by_region": {"Bavaria": 1},
    }


def test_duplicate_upload_returns_conflict(client: TestClient) -> None:
    assert _upload_text(client).status_code == 201

    duplicate = client.post(
        "/documents",
        data={**DOCUMENT_FORM, "title": "A different title"},
        files={"file": ("renamed.txt", b"Bridge reinforcement programme", "text/plain")},
    )

    assert duplicate.status_code == 409
    assert "already exists" in duplicate.json()["detail"]


@pytest.mark.parametrize(
    ("filename", "content", "expected_status"),
    [
        ("photo.jpg", b"not really an image", 415),
        ("empty.txt", b"", 400),
    ],
)
def test_upload_rejects_unsupported_and_empty_files(
    client: TestClient,
    filename: str,
    content: bytes,
    expected_status: int,
) -> None:
    response = client.post(
        "/documents",
        data=DOCUMENT_FORM,
        files={"file": (filename, content, "application/octet-stream")},
    )

    assert response.status_code == expected_status
