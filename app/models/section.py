from pydantic import BaseModel


class Section(BaseModel):
  title: str | None = None
  order: int
  text: str
