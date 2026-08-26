from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import connection as db_connection
from app.main import app


PROJECT_ROOT = Path(__file__).parents[1]


@pytest.fixture(autouse=True)
def test_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Path]:
    """Give every test a fresh database using the production schema."""
    database_path = tmp_path / "infrastructure-test.db"
    schema_path = PROJECT_ROOT / "app" / "db" / "schema.sql"

    monkeypatch.setattr(db_connection, "DATABASE_PATH", database_path)
    monkeypatch.setattr(db_connection, "SCHEMA_PATH", schema_path)
    db_connection.initialize_database()

    yield database_path


@pytest.fixture
def client(test_database: Path) -> Iterator[TestClient]:
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
