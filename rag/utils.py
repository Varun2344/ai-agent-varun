# rag/utils.py (Corrected Version with Bug Fix)
import re

def clean_text(text: str) -> str:
    """Removes extra whitespace from text."""
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def chunk_text(text: str, max_chars: int = 800, overlap: int = 100):
    """
    Splits text into overlapping chunks.
    This corrected version ensures the loop always makes progress and terminates correctly.
    """
    if not text:
        return []
        
    chunks = []
    start = 0
    
    # Calculate the step size, ensuring it's positive to prevent infinite loops
    step = max_chars - overlap
    if step <= 0:
        raise ValueError("max_chars must be greater than overlap to avoid an infinite loop.")

    # Loop through the text and create chunks
    while start < len(text):
        end = start + max_chars
        chunk = text[start:end]
        chunks.append(chunk)
        start += step
        
    return chunks