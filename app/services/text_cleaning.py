import re
import unicodedata


def clean_text(text: str):
  text = unicodedata.normalize("NFKC",text)
  # normalize newlines
  text = text.replace("\r\n","\n")
  text = text.replace("\r","\n")
  # normalize horizontal whitespace
  text = re.sub(r"[ \t\f\v]+", " ", text)

  lines = [line.strip() for line in text.split("\n")]
  cleaned_lines:list[str] = []
  prev_was_empty = False

  for line in lines:
    if not line:
      if not prev_was_empty:
        cleaned_lines.append("")

      prev_was_empty= True
      continue
    cleaned_lines.append(line)
    prev_was_empty = False

  return "\n".join(cleaned_lines).strip()
