from pydantic import BaseModel


class StatsResponse(BaseModel):
    documents_indexed: int
    sections_indexed: int
    characters_indexed: int
    documents_by_file_type: dict[str, int]
    documents_by_category: dict[str, int]
    documents_by_region: dict[str, int]
