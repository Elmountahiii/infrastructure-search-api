import re

from app.models.section import Section


HEADING_PATTERN = re.compile(r"^#{1,6}\s+(.+)$")


def split_large_section(
    text: str,
    max_chars: int,
) -> list[str]:
    if len(text) <= max_chars:
        return [text]

    paragraphs = [
        paragraph.strip()
        for paragraph in text.split("\n\n")
        if paragraph.strip()
    ]

    chunks: list[str] = []
    current_chunk: list[str] = []
    current_length = 0

    for paragraph in paragraphs:
        paragraph_length = len(paragraph)

        if (
            current_chunk
            and current_length + paragraph_length > max_chars
        ):
            chunks.append("\n\n".join(current_chunk))

            current_chunk = []
            current_length = 0

        current_chunk.append(paragraph)
        current_length += paragraph_length

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    return chunks



def split_into_sections(
    text: str,
    max_chars: int = 3000,
) -> list[Section]:
    lines = text.splitlines()

    raw_sections: list[tuple[str | None, str]] = []

    current_title: str | None = None
    current_lines: list[str] = []

    for line in lines:
        heading_match = HEADING_PATTERN.match(line.strip())

        if heading_match:
            if current_lines:
                section_text = "\n".join(current_lines).strip()

                if section_text:
                    raw_sections.append(
                        (current_title, section_text)
                    )

            current_title = heading_match.group(1).strip()
            current_lines = []

        else:
            current_lines.append(line)

    if current_lines:
        section_text = "\n".join(current_lines).strip()

        if section_text:
            raw_sections.append(
                (current_title, section_text)
            )

    sections: list[Section] = []

    for title, section_text in raw_sections:
        chunks = split_large_section(
            section_text,
            max_chars=max_chars,
        )

        for chunk in chunks:
            sections.append(
                Section(
                    title=title,
                    order=len(sections),
                    text=chunk,
                )
            )

    return sections
