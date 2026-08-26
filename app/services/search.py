from datetime import date
import re
import sqlite3

from app.db.connection import get_connection
from app.models.search import SearchResult


class InvalidSearchQueryError(Exception):
    pass


def _is_fts_query_error(
    error: sqlite3.OperationalError,
    query: str,
) -> bool:
    message = str(error).lower()

    if any(
        marker in message
        for marker in (
            "fts5: syntax error",
            "malformed match expression",
            "unterminated string",
        )
    ):
        return True

    if message.startswith("no such column:"):
        column = message.removeprefix("no such column:").strip()
        return f"{column}:" in query.lower()

    return False


def search_documents(
    query: str,
    category: str | None = None,
    region: str | None = None,
    source: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 20,
) -> list[SearchResult]:
    connection = get_connection()

    try:
        conditions = ["sections_fts MATCH ?"]
        params: list[object] = [query]

        if category:
            conditions.append("d.category = ?")
            params.append(category)

        if region:
            conditions.append("d.region = ?")
            params.append(region)

        if source:
            conditions.append("d.source = ?")
            params.append(source)

        if date_from:
            conditions.append("d.publication_date >= ?")
            params.append(date_from.isoformat())

        if date_to:
            conditions.append("d.publication_date <= ?")
            params.append(date_to.isoformat())

        where_clause = " AND ".join(conditions)

        try:
            rows = connection.execute(
                f"""
                SELECT
                    d.id AS document_id,
                    s.id AS section_id,
                    d.title,
                    s.section_title,

                    snippet(
                        sections_fts,
                        1,
                        '[',
                        ']',
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

                WHERE {where_clause}

                ORDER BY bm25(sections_fts)

                LIMIT ?
                """,
                (*params, limit),
            ).fetchall()

        except sqlite3.OperationalError as exc:
            if _is_fts_query_error(exc, query):
                raise InvalidSearchQueryError(
                    "Invalid FTS5 query"
                ) from exc

            raise

        results = []

        for row in rows:
            data = dict(row)

            data["snippet"] = re.sub(
                r"\s+",
                " ",
                data["snippet"],
            ).strip()

            results.append(SearchResult(**data))

        return results

    finally:
        connection.close()
