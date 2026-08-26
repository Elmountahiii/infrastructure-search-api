from app.services.sectioning import split_into_sections


def test_split_into_structural_sections_in_order() -> None:
    text = """# Report

Introduction.

## Bridges

Bridge content.

## Railways

Rail content."""

    sections = split_into_sections(text)

    assert len(sections) == 3
    assert [section.title for section in sections] == ["Report", "Bridges", "Railways"]
    assert [section.order for section in sections] == [0, 1, 2]
    assert sections[0].text == "Introduction."
    assert sections[1].text == "Bridge content."
    assert sections[2].text == "Rail content."


def test_oversized_section_splits_at_paragraph_boundaries() -> None:
    text = "# Bridges\n\nFirst bridge paragraph.\n\nSecond bridge paragraph."

    sections = split_into_sections(text, max_chars=30)

    assert len(sections) == 2
    assert [section.text for section in sections] == [
        "First bridge paragraph.",
        "Second bridge paragraph.",
    ]
    assert [section.title for section in sections] == ["Bridges", "Bridges"]
    assert [section.order for section in sections] == [0, 1]
