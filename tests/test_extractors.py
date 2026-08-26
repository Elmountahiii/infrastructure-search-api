from app.extractors.html import extract_html
from app.extractors.markdown import extract_markdown
from app.extractors.pdf import extract_pdf_pages
from app.extractors.text import extract_text


def _make_tiny_pdf(text: str) -> bytes:
    """Build a one-page, dependency-free PDF containing simple ASCII text."""
    escaped_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content_stream = f"BT /F1 12 Tf 72 720 Td ({escaped_text}) Tj ET".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        (
            f"<< /Length {len(content_stream)} >>\nstream\n".encode("ascii")
            + content_stream
            + b"\nendstream"
        ),
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode("ascii"))
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return bytes(pdf)


def test_extract_text_decodes_utf8() -> None:
    assert extract_text(b"Bridge maintenance report") == "Bridge maintenance report"


def test_extract_text_removes_utf8_bom() -> None:
    content = b"\xef\xbb\xbfBridge maintenance report"
    assert extract_text(content) == "Bridge maintenance report"


def test_extract_markdown_preserves_readable_structure() -> None:
    content = b"# Infrastructure Report\n\n## Bridges\n\nBridge maintenance is required."

    result = extract_markdown(content)

    assert "# Infrastructure Report" in result
    assert "## Bridges" in result
    assert "Bridge maintenance is required." in result


def test_extract_html_keeps_content_and_removes_page_chrome() -> None:
    content = b"""
        <html>
          <head><style>body { color: red; }</style></head>
          <body>
            <nav>Home</nav>
            <h1>Rail Infrastructure</h1>
            <p>Bridge maintenance is required.</p>
            <script>alert("x")</script>
          </body>
        </html>
    """

    result = extract_html(content)

    assert "# Rail Infrastructure" in result
    assert "Bridge maintenance is required." in result
    assert "Home" not in result
    assert "color: red" not in result
    assert "alert" not in result


def test_extract_pdf_reads_page_count_and_known_text() -> None:
    pages = extract_pdf_pages(_make_tiny_pdf("Regional bridge report"))

    assert len(pages) == 1
    assert "Regional bridge report" in pages[0]
