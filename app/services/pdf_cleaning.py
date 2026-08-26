from collections import Counter
import re


def normalize_repeated_line(line: str) -> str:
    line = line.strip().lower()
    line = re.sub(r"\d+", "#", line)
    line = re.sub(r"\s+", " ", line)

    return line

def find_repeated_lines(
    pages: list[str],
    position: str,
    line_count: int = 3,
    threshold: float = 0.6,
) -> set[str]:
    counts = Counter()

    for page in pages:
        lines = [line.strip() for line in page.splitlines() if line.strip()]

        if position == "top":
            candidates = lines[:line_count]
        else:
            candidates = lines[-line_count:]

        normalized_candidates = {
            normalize_repeated_line(line)
            for line in candidates
        }

        counts.update(normalized_candidates)

    minimum_count = len(pages) * threshold

    return {
        line
        for line, count in counts.items()
        if count >= minimum_count
    }

def remove_repeated_headers_footers(
    pages: list[str],
    line_count: int = 3,
    threshold: float = 0.6,
) -> list[str]:
    repeated_headers = find_repeated_lines(
        pages,
        position="top",
        line_count=line_count,
        threshold=threshold,
    )

    repeated_footers = find_repeated_lines(
        pages,
        position="bottom",
        line_count=line_count,
        threshold=threshold,
    )

    cleaned_pages = []

    for page in pages:
        lines = page.splitlines()

        cleaned_lines = []

        for index, line in enumerate(lines):
            normalized = normalize_repeated_line(line)

            is_header_area = index < line_count
            is_footer_area = index >= len(lines) - line_count

            if is_header_area and normalized in repeated_headers:
                continue

            if is_footer_area and normalized in repeated_footers:
                continue

            cleaned_lines.append(line)

        cleaned_pages.append("\n".join(cleaned_lines))

    return cleaned_pages
