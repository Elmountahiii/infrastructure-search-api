from datetime import date

from pydantic import BaseModel, HttpUrl


class DocumentCreate(BaseModel):
  title: str
  source: str
  url: HttpUrl | None = None
  category: str
  region: str
  publication_date: date | None = None
