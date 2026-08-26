from datetime import date, datetime

from pydantic import BaseModel, HttpUrl

from app.models.section import SectionResponse


class DocumentCreate(BaseModel):
  title: str
  source: str
  url: HttpUrl | None = None
  category: str
  region: str
  publication_date: date | None = None


class DocumentResponse(BaseModel):
    id: int
    title: str
    source: str
    url: str | None
    category: str
    region: str
    publication_date: date | None
    file_type: str
    created_at: datetime


class DocumentSummary(DocumentResponse):
    sections_count: int


class DocumentDetail(DocumentResponse):
    sections: list[SectionResponse]
