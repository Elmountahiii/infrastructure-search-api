from app.db.connection import get_connection
from app.models.document import DocumentCreate
from app.models.section import Section

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
            raise ValueError(
                f"Duplicate document: existing document id={existing['id']}"
            )

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
