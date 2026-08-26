from datetime import date

import pytest

from app.models.document import DocumentCreate
from app.models.section import Section
from app.services.content_hashing import calculate_content_hash
from app.services.document_storage import (
    DuplicateDocumentError,
    get_document,
    get_documents,
    save_document,
)


def _document(title: str = "Infrastructure report") -> DocumentCreate:
    return DocumentCreate(
        title=title,
        source="Regional Authority",
        category="transport",
        region="Bavaria",
        publication_date=date(2025, 4, 10),
    )


def test_save_document_persists_ordered_sections() -> None:
    sections = [
        Section(title="Bridges", order=0, text="Bridge maintenance."),
        Section(title="Railways", order=1, text="Rail upgrades."),
    ]

    document_id = save_document(
        document=_document(),
        file_type="txt",
        content_hash=calculate_content_hash("Bridge maintenance. Rail upgrades."),
        sections=sections,
    )

    saved = get_document(document_id)
    assert saved is not None
    assert saved.id == document_id
    assert saved.title == "Infrastructure report"
    assert [section.section_title for section in saved.sections] == ["Bridges", "Railways"]
    assert [section.section_order for section in saved.sections] == [0, 1]
    assert [section.text for section in saved.sections] == [
        "Bridge maintenance.",
        "Rail upgrades.",
    ]


def test_duplicate_hash_is_rejected_and_original_remains() -> None:
    content_hash = calculate_content_hash("Same normalized content")
    sections = [Section(title=None, order=0, text="Same normalized content")]
    original_id = save_document(_document(), "txt", content_hash, sections)

    with pytest.raises(DuplicateDocumentError) as error:
        save_document(
            _document(title="Different filename and metadata"),
            "md",
            content_hash,
            sections,
        )

    assert error.value.document_id == original_id
    assert [document.id for document in get_documents()] == [original_id]
