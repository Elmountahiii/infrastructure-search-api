from datetime import date

import pytest

from app.models.document import DocumentCreate
from app.models.section import Section
from app.services.content_hashing import calculate_content_hash
from app.services.document_storage import save_document
from app.services.search import InvalidSearchQueryError, search_documents


def _save_searchable_document(
    *,
    title: str,
    text: str,
    source: str = "Regional Authority",
    region: str = "Bavaria",
    category: str = "transport",
    publication_date: date | None = None,
) -> int:
    document = DocumentCreate(
        title=title,
        source=source,
        region=region,
        category=category,
        publication_date=publication_date,
    )
    return save_document(
        document=document,
        file_type="txt",
        content_hash=calculate_content_hash(text),
        sections=[Section(title="Programme", order=0, text=text)],
    )


def test_fts_search_returns_result_fields_and_clean_highlighted_snippet() -> None:
    document_id = _save_searchable_document(
        title="Bridge programme",
        text="The regional bridge\nreinforcement programme is funded.",
        publication_date=date(2025, 4, 10),
    )

    results = search_documents("bridge")

    assert len(results) == 1
    result = results[0]
    assert result.document_id == document_id
    assert result.section_id > 0
    assert result.title == "Bridge programme"
    assert result.section_title == "Programme"
    assert result.source == "Regional Authority"
    assert result.region == "Bavaria"
    assert result.category == "transport"
    assert result.publication_date == date(2025, 4, 10)
    assert "[bridge]" in result.snippet
    assert "\n" not in result.snippet
    assert isinstance(result.score, float)


def test_metadata_filters_only_return_the_matching_document() -> None:
    bavaria_id = _save_searchable_document(
        title="Bavaria transport",
        text="Shared resilience programme for bridges in Bavaria.",
        source="Transport Office",
        region="Bavaria",
        category="transport",
    )
    hesse_id = _save_searchable_document(
        title="Hesse energy",
        text="Shared resilience programme for energy in Hesse.",
        source="Energy Office",
        region="Hesse",
        category="energy",
    )

    assert [item.document_id for item in search_documents("resilience", region="Bavaria")] == [
        bavaria_id
    ]
    assert [item.document_id for item in search_documents("resilience", category="energy")] == [
        hesse_id
    ]
    assert [
        item.document_id for item in search_documents("resilience", source="Transport Office")
    ] == [bavaria_id]


def test_date_filters_support_open_and_closed_ranges() -> None:
    ids_by_date = {
        date(2024, 5, 1): _save_searchable_document(
            title="2024 report",
            text="Corridor renewal programme phase alpha.",
            publication_date=date(2024, 5, 1),
        ),
        date(2025, 4, 10): _save_searchable_document(
            title="2025 report",
            text="Corridor renewal programme phase beta.",
            publication_date=date(2025, 4, 10),
        ),
        date(2026, 2, 1): _save_searchable_document(
            title="2026 report",
            text="Corridor renewal programme phase gamma.",
            publication_date=date(2026, 2, 1),
        ),
    }

    from_results = search_documents("renewal", date_from=date(2025, 1, 1))
    to_results = search_documents("renewal", date_to=date(2025, 12, 31))
    range_results = search_documents(
        "renewal",
        date_from=date(2025, 1, 1),
        date_to=date(2025, 12, 31),
    )

    assert {item.document_id for item in from_results} == {
        ids_by_date[date(2025, 4, 10)],
        ids_by_date[date(2026, 2, 1)],
    }
    assert {item.document_id for item in to_results} == {
        ids_by_date[date(2024, 5, 1)],
        ids_by_date[date(2025, 4, 10)],
    }
    assert [item.document_id for item in range_results] == [ids_by_date[date(2025, 4, 10)]]


def test_stronger_term_match_is_ranked_first() -> None:
    weak_id = _save_searchable_document(
        title="General works",
        text="Bridge planning includes surveys, procurement, and community consultation.",
    )
    strong_id = _save_searchable_document(
        title="Bridge works",
        text="Bridge bridge bridge bridge reinforcement.",
    )

    results = search_documents("bridge")

    assert results[0].document_id == strong_id
    assert {result.document_id for result in results} == {strong_id, weak_id}


def test_malformed_fts_query_has_a_domain_error() -> None:
    _save_searchable_document(
        title="Query validation fixture",
        text="Bridge query validation content.",
    )

    with pytest.raises(InvalidSearchQueryError):
        search_documents('"')
