from bs4 import BeautifulSoup

def extract_html(content: bytes):
  soup = BeautifulSoup(content,"html.parser")
  for tag in soup(["script", "style", "noscript", "nav"]):
    tag.decompose()

  for level in range(1,7):
    for headline in soup.find_all(f"h{level}"):
      text = headline.get_text(" ",strip=True)
      headline.replace_with(f"\n{'#' * level} {text}\n")

  return soup.get_text(separator="\n",strip=True)
