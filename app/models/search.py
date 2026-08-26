from datetime import date

from pydantic import BaseModel


class SearchResult(BaseModel):
    document_id: int
    section_id: int
    title: str
    section_title: str | None
    snippet: str
    source: str
    url: str | None
    region: str
    category: str
    publication_date: date | None
    score: float
