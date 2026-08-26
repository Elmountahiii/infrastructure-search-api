from app.db.connection import get_connection
from app.models.document import DocumentCreate, DocumentDetail, DocumentSummary
from app.models.section import Section, SectionResponse


class DuplicateDocumentError(Exception):
    def __init__(self, document_id: int) -> None:
        self.document_id = document_id
        super().__init__(f"Document already exists with id {document_id}")


def find_document_by_hash(content_hash: str) -> int | None:
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT id
            FROM documents
            WHERE content_hash = ?
            """,
            (content_hash,),
        ).fetchone()

        if row is None:
            return None

        return row["id"]

    finally:
        connection.close()


def get_documents() -> list[DocumentSummary]:
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                d.id,
                d.title,
                d.source,
                d.url,
                d.category,
                d.region,
                d.publication_date,
                d.file_type,
                d.created_at,
                COUNT(s.id) AS sections_count
            FROM documents AS d
            LEFT JOIN sections AS s
                ON s.document_id = d.id
            GROUP BY d.id
            ORDER BY d.id
            """
        ).fetchall()

        return [DocumentSummary(**dict(row)) for row in rows]

    finally:
        connection.close()


def get_document(document_id: int) -> DocumentDetail | None:
    connection = get_connection()

    try:
        document_row = connection.execute(
            """
            SELECT
                id,
                title,
                source,
                url,
                category,
                region,
                publication_date,
                file_type,
                created_at
            FROM documents
            WHERE id = ?
            """,
            (document_id,),
        ).fetchone()

        if document_row is None:
            return None

        section_rows = connection.execute(
            """
            SELECT
                id,
                section_title,
                section_order,
                text
            FROM sections
            WHERE document_id = ?
            ORDER BY section_order
            """,
            (document_id,),
        ).fetchall()

        sections = [
            SectionResponse(**dict(row))
            for row in section_rows
        ]

        return DocumentDetail(
            **dict(document_row),
            sections=sections,
        )

    finally:
        connection.close()


def save_document(
    document: DocumentCreate,
    file_type: str,
    content_hash: str,
    sections: list[Section],
) -> int:
    connection = get_connection()

    try:
        existing = connection.execute(
            """
            SELECT id
            FROM documents
            WHERE content_hash = ?
            """,
            (content_hash,),
        ).fetchone()

        if existing:
            raise DuplicateDocumentError(existing["id"])

        cursor = connection.execute(
            """
            INSERT INTO documents (
                title,
                source,
                url,
                category,
                region,
                publication_date,
                file_type,
                content_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document.title,
                document.source,
                str(document.url) if document.url else None,
                document.category,
                document.region,
                (
                    document.publication_date.isoformat()
                    if document.publication_date
                    else None
                ),
                file_type,
                content_hash,
            ),
        )

        document_id = cursor.lastrowid

        if document_id is None:
            raise RuntimeError("Failed to create document")

        for section in sections:
            connection.execute(
                """
                INSERT INTO sections (
                    document_id,
                    section_title,
                    section_order,
                    text
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    document_id,
                    section.title,
                    section.order,
                    section.text,
                ),
            )

        connection.commit()

        return document_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
