from pydantic import BaseModel


class IngestionResult(BaseModel):
    document_id: int
    status: str
    sections_indexed: int
