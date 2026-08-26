from bs4.exceptions import ParserRejectedMarkup
from pypdf.errors import PyPdfError

from app.extractors.html import extract_html
from app.extractors.markdown import extract_markdown
from app.extractors.pdf import extract_pdf_pages
from app.extractors.text import extract_text
from app.services.pdf_cleaning import remove_repeated_headers_footers
from app.services.text_cleaning import clean_text


class DocumentExtractionError(Exception):
    pass


def extract_document(content: bytes, file_type: str) -> str:
    file_type = file_type.lower().lstrip(".")

    try:
        if file_type == "txt":
            text = extract_text(content)

        elif file_type in {"md", "markdown"}:
            text = extract_markdown(content)

        elif file_type in {"html", "htm"}:
            text = extract_html(content)

        elif file_type == "pdf":
            pages = extract_pdf_pages(content)

            pages = [
                clean_text(page)
                for page in pages
            ]

            pages = remove_repeated_headers_footers(pages)

            text = "\n\n".join(pages)

        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        return clean_text(text)

    except (
        ParserRejectedMarkup,
        PyPdfError,
        UnicodeError,
        ValueError,
    ) as exc:
        raise DocumentExtractionError(
            "Unable to extract document"
        ) from exc
