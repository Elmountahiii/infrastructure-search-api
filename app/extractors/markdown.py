from app.extractors.text import extract_text


def extract_markdown(content: bytes):
  return extract_text(content)
