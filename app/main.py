from pathlib import Path

from fastapi import FastAPI

from app.models.document import DocumentCreate


app = FastAPI(
    title="Infrastructure Search API",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/document")
def create_document(document:DocumentCreate):
  return document
