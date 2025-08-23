
import requests
from bs4 import BeautifulSoup

def fetch_url(url: str, max_chars: int = 2000) -> str:
    if not url or not url.startswith(("http://","https://")):
        return "[error] provide a full http(s) URL."
    try:
        r = requests.get(url, timeout=12, headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script","style","noscript"]): tag.decompose()
        text = soup.get_text(separator=" ").strip()
        return text[:max_chars] if text else "[warn] empty page text"
    except Exception as e:
        return f"[error] fetch_url failed: {e}"
