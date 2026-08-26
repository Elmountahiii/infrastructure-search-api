from app.db.connection import get_connection
from app.models.stats import StatsResponse


def get_stats() -> StatsResponse:
    connection = get_connection()

    try:
        documents_row = connection.execute(
            """
            SELECT COUNT(*) AS documents_indexed
            FROM documents
            """
        ).fetchone()

        sections_row = connection.execute(
            """
            SELECT
                COUNT(*) AS sections_indexed,
                COALESCE(SUM(LENGTH(text)), 0) AS characters_indexed
            FROM sections
            """
        ).fetchone()

        file_type_rows = connection.execute(
            """
            SELECT file_type, COUNT(*) AS count
            FROM documents
            GROUP BY file_type
            ORDER BY file_type
            """
        ).fetchall()

        category_rows = connection.execute(
            """
            SELECT category, COUNT(*) AS count
            FROM documents
            GROUP BY category
            ORDER BY category
            """
        ).fetchall()

        region_rows = connection.execute(
            """
            SELECT region, COUNT(*) AS count
            FROM documents
            GROUP BY region
            ORDER BY region
            """
        ).fetchall()

        return StatsResponse(
            documents_indexed=documents_row["documents_indexed"],
            sections_indexed=sections_row["sections_indexed"],
            characters_indexed=sections_row["characters_indexed"],
            documents_by_file_type={
                row["file_type"]: row["count"]
                for row in file_type_rows
            },
            documents_by_category={
                row["category"]: row["count"]
                for row in category_rows
            },
            documents_by_region={
                row["region"]: row["count"]
                for row in region_rows
            },
        )

    finally:
        connection.close()
