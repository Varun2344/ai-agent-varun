
import re

def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "")
    return text.strip()

def chunk_text(text: str, max_chars: int = 800, overlap: int = 100):
    text = text or ""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        if start < 0: start = 0
        if start >= len(text): break
    return chunks
