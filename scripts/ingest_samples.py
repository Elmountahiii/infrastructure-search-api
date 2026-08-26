import os
import time
from pathlib import Path

import httpx


API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
SAMPLES_DIR = Path(os.getenv("SAMPLES_DIR", "samples"))
HEALTH_CHECK_ATTEMPTS = int(os.getenv("HEALTH_CHECK_ATTEMPTS", "30"))
HEALTH_CHECK_INTERVAL = float(os.getenv("HEALTH_CHECK_INTERVAL", "1"))


DOCUMENTS = [
    {
        "filename": "FRP_Autobahn_GmbH_2025-2029.pdf",
        "title": "Finanzierungs- und Realisierungsplan 2025-2029",
        "source": "Die Autobahn GmbH des Bundes",
        "url": (
            "https://www.autobahn.de/planen-bauen/"
            "finanzierungs-und-realisierungsplaene"
        ),
        "category": "transport",
        "region": "Germany",
        "publication_date": None,
    },
    {
        "filename": "infrastructure-strategy.html",
        "title": "10 Year Infrastructure Strategy Working Paper",
        "source": "HM Treasury",
        "url": (
            "https://www.gov.uk/government/publications/"
            "10-year-infrastructure-strategy-working-paper"
        ),
        "category": "infrastructure",
        "region": "United Kingdom",
        "publication_date": "2025-01-26",
    },
    {
        "filename": "autobahn-api.md",
        "title": "Autobahn API Documentation",
        "source": "BundesAPI",
        "url": (
            "https://github.com/bundesAPI/deutschland/"
            "tree/main/docs/autobahn"
        ),
        "category": "transport",
        "region": "Germany",
        "publication_date": None,
    },
    {
        "filename": "swu-agency.txt",
        "title": "SWU Verkehr GTFS Agency Data",
        "source": "SWU Verkehr GmbH",
        "url": (
            "https://www.swu.de/privatkunden/service/"
            "nahverkehr/gtfs-daten"
        ),
        "category": "transport",
        "region": "Baden-Württemberg",
        "publication_date": None,
    },
]


def wait_for_api(client: httpx.Client) -> None:
    for attempt in range(1, HEALTH_CHECK_ATTEMPTS + 1):
        try:
            response = client.get(f"{API_URL}/health")
            response.raise_for_status()
            return
        except httpx.HTTPError as exc:
            if attempt == HEALTH_CHECK_ATTEMPTS:
                raise RuntimeError(
                    f"API did not become ready at {API_URL}"
                ) from exc

            time.sleep(HEALTH_CHECK_INTERVAL)


def ingest_document(client: httpx.Client, document: dict) -> bool:
    path = SAMPLES_DIR / document["filename"]

    if not path.exists():
        print(f"✗ Missing: {path}")
        return False

    data = {
        "title": document["title"],
        "source": document["source"],
        "url": document["url"],
        "category": document["category"],
        "region": document["region"],
    }

    if document["publication_date"]:
        data["publication_date"] = document["publication_date"]

    with path.open("rb") as file:
        files = {
            "file": (
                path.name,
                file,
                "application/octet-stream",
            )
        }

        response = client.post(
            f"{API_URL}/documents",
            data=data,
            files=files,
        )

    if response.status_code == 201:
        result = response.json()

        print(
            f"✓ {path.name} "
            f"-> document_id={result['document_id']} "
            f"sections={result['sections_indexed']}"
        )
        return True

    elif response.status_code == 409:
        print(f"↷ {path.name} -> already indexed")
        return True

    else:
        print(
            f"✗ {path.name} "
            f"-> HTTP {response.status_code}: "
            f"{response.text}"
        )
        return False


def main() -> None:
    print(f"Ingesting {len(DOCUMENTS)} sample documents...\n")

    with httpx.Client(timeout=60.0) as client:
        wait_for_api(client)

        successful = sum(
            ingest_document(client, document)
            for document in DOCUMENTS
        )

    if successful != len(DOCUMENTS):
        raise RuntimeError(
            f"Failed to ingest {len(DOCUMENTS) - successful} sample document(s)"
        )

    print("\nDone.")


if __name__ == "__main__":
    main()
