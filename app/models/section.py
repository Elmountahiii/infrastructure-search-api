from pydantic import BaseModel


class Section(BaseModel):
  title: str | None = None
  order: int
  text: str


class SectionResponse(BaseModel):
    id: int
    section_title: str | None
    section_order: int
    text: str
