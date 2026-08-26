from app.services.content_hashing import calculate_content_hash
from app.services.pdf_cleaning import remove_repeated_headers_footers
from app.services.text_cleaning import clean_text


def test_clean_text_collapses_horizontal_whitespace() -> None:
    assert clean_text("Railway      infrastructure") == "Railway infrastructure"


def test_clean_text_collapses_excessive_empty_lines() -> None:
    assert clean_text("Railway\n\n\n\nBridge") == "Railway\n\nBridge"


def test_clean_text_applies_unicode_compatibility_normalization() -> None:
    assert clean_text("ﬁbre") == "fibre"


def test_remove_repeated_pdf_headers_and_numbered_footers() -> None:
    pages = [
        "Infrastructure Report\nBridge maintenance continues.\nPriority works.\nPage 1",
        "Infrastructure Report\nRailway upgrades continue.\nTrack works.\nPage 2",
        "Infrastructure Report\nWater upgrades continue.\nPipeline works.\nPage 3",
    ]

    cleaned = remove_repeated_headers_footers(pages)

    assert all("Infrastructure Report" not in page for page in cleaned)
    assert all("Page " not in page for page in cleaned)
    assert "Bridge maintenance continues." in cleaned[0]
    assert "Railway upgrades continue." in cleaned[1]
    assert "Water upgrades continue." in cleaned[2]


def test_repeated_phrase_in_middle_of_pdf_page_is_preserved() -> None:
    pages = [
        (
            "Infrastructure Report\nBridge maintenance.\nPriority works.\n"
            "Infrastructure Report\nAdditional detail.\nPage 1"
        ),
        (
            "Infrastructure Report\nRailway upgrades.\nTrack works.\n"
            "Delivery schedule\nAdditional milestones.\nPage 2"
        ),
        (
            "Infrastructure Report\nWater upgrades.\nPipeline works.\n"
            "Funding schedule\nAdditional approvals.\nPage 3"
        ),
    ]

    cleaned = remove_repeated_headers_footers(pages)

    assert cleaned[0].count("Infrastructure Report") == 1


def test_content_hash_contract() -> None:
    normalized = clean_text("Bridge      maintenance")
    equivalent = clean_text("Bridge maintenance")

    assert calculate_content_hash(normalized) == calculate_content_hash(equivalent)
    assert calculate_content_hash(normalized) != calculate_content_hash("Rail maintenance")
