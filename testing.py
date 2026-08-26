from datetime import date
from pathlib import Path

from app.db.connection import get_connection, initialize_database
from app.extractors.pdf import extract_pdf_pages
from app.models.document import DocumentCreate
from app.services.content_hashing import calculate_content_hash
from app.services.document_extraction import extract_document
from app.services.document_storage import save_document
from app.services.pdf_cleaning import remove_repeated_headers_footers
from app.services.search import search_documents
from app.services.sectioning import split_into_sections
from app.services.text_cleaning import clean_text


PROJECT_ROOT = Path(__file__).parent


def main() -> None:
  results = search_documents(
      query="Heathrow",

  )
  for result in results:
      print("---")
      print("TITLE:", result.title)
      print("SECTION:", result.section_title)
      print("SCORE:", result.score)
      print("SNIPPET:", result.snippet)

    # print("------ SECTIONS -------")
    # for section in sections:
    # print(f"index: {section.order} :\ntitle: {section.title}:\ntext: {section.text}\n")
    # doc = DocumentCreate(
    #   title="ties-one-year-on-annex.pdf",
    #   source="Fictional Regional Authority",
    #   category="transportation",
    #   region="London",
    #   publication_date=date.fromisoformat("2025-04-10"),
    # )
    # docId = save_document(document=doc,content_hash=content_hash,file_type="pdf",sections=sections)
    # print(f"docId: {docId}")

if __name__ == "__main__":
    main()
