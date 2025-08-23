# rag/ingest.py (Memory-Efficient Version)

import os
import argparse
import uuid
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from rag.utils import clean_text, chunk_text

def read_url(url: str) -> str:
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator=" ")
        return clean_text(text)
    except Exception as e:
        print(f"[ERROR] Failed to fetch {url}: {e}")
        return None

def read_pdf(path: str) -> str:
    try:
        reader = PdfReader(path)
        text = " ".join([p.extract_text() or "" for p in reader.pages])
        return clean_text(text)
    except Exception as e:
        print(f"[ERROR] Failed to read {path}: {e}")
        return None

def main(persist_dir: str, urls_file: str | None, pdf_dir: str | None):
    print("\n\n✅✅✅ WE ARE RUNNING THE CORRECT SCRIPT! ✅✅✅\n\n")
    print("Initializing ChromaDB and Sentence Transformer model...")
    os.makedirs(persist_dir, exist_ok=True)
    client = chromadb.PersistentClient(path=persist_dir, settings=Settings(allow_reset=True))
    col = client.get_or_create_collection("docs")
    encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    print("Initialization complete.")

    total_chunks_ingested = 0

    # Process URLs
    if urls_file and os.path.exists(urls_file):
        with open(urls_file, "r", encoding="utf-8") as f:
            for url in f:
                url = url.strip()
                if not url:
                    continue
                
                print(f"\n--- Processing URL: {url} ---")
                txt = read_url(url)
                if not txt:
                    continue

                chunks = chunk_text(txt)
                if not chunks:
                    print("No text chunks generated.")
                    continue
                    
                ids = [str(uuid.uuid4()) for _ in chunks]
                metadatas = [{"source": url, "kind": "url"} for _ in chunks]
                
                print(f"Embedding and adding {len(chunks)} chunks to the database...")
                emb = encoder.encode(chunks, normalize_embeddings=True, show_progress_bar=True).tolist()
                col.add(documents=chunks, metadatas=metadatas, ids=ids, embeddings=emb)
                total_chunks_ingested += len(chunks)
                print(f"Successfully added chunks for {url}")

    # Process PDFs
    if pdf_dir and os.path.isdir(pdf_dir):
        for name in os.listdir(pdf_dir):
            if not name.lower().endswith(".pdf"):
                continue
            
            path = os.path.join(pdf_dir, name)
            print(f"\n--- Processing PDF: {name} ---")
            txt = read_pdf(path)
            if not txt:
                continue

            chunks = chunk_text(txt)
            if not chunks:
                print("No text chunks generated.")
                continue

            ids = [str(uuid.uuid4()) for _ in chunks]
            metadatas = [{"source": name, "kind": "pdf"} for _ in chunks]
            
            print(f"Embedding and adding {len(chunks)} chunks to the database...")
            emb = encoder.encode(chunks, normalize_embeddings=True, show_progress_bar=True).tolist()
            col.add(documents=chunks, metadatas=metadatas, ids=ids, embeddings=emb)
            total_chunks_ingested += len(chunks)
            print(f"Successfully added chunks for {name}")

    if total_chunks_ingested == 0:
        print("\nNo documents were found or processed. The database might be empty.")
    else:
        print(f"\n✅ Ingestion complete. Total chunks added: {total_chunks_ingested}. Persisted to {persist_dir}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--persist_dir", default="./db")
    ap.add_argument("--urls", default="domain/demo/seed_urls.txt")
    ap.add_argument("--pdf_dir", default="domain/demo/seed_pdfs")
    args = ap.parse_args()
    main(args.persist_dir, args.urls, args.pdf_dir)