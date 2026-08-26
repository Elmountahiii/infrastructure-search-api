from app.db.connection import get_connection
from app.models.search import SearchResult


def search_documents(
    query: str,
    limit: int = 20,
) -> list[SearchResult]:
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                d.id AS document_id,
                s.id AS section_id,
                d.title,
                s.section_title,

                snippet(
                    sections_fts,
                    1,
                    '<mark>',
                    '</mark>',
                    '...',
                    25
                ) AS snippet,

                d.source,
                d.url,
                d.region,
                d.category,
                d.publication_date,

                -bm25(sections_fts) AS score

            FROM sections_fts

            JOIN sections AS s
                ON s.id = sections_fts.rowid

            JOIN documents AS d
                ON d.id = s.document_id

            WHERE sections_fts MATCH ?

            ORDER BY bm25(sections_fts)

            LIMIT ?
            """,
            (query, limit),
        ).fetchall()

        return [
            SearchResult(**dict(row))
            for row in rows
        ]

    finally:
        connection.close()
