
import os, argparse, uuid, requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from .utils import clean_text, chunk_text

def read_url(url: str) -> str:
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script","style","noscript"]): tag.decompose()
        text = soup.get_text(separator=" ")
        return clean_text(text)
    except Exception as e:
        return f"[error] failed to fetch {url}: {e}"

def read_pdf(path: str) -> str:
    try:
        reader = PdfReader(path)
        text = " ".join([p.extract_text() or "" for p in reader.pages])
        return clean_text(text)
    except Exception as e:
        return f"[error] failed to read {path}: {e}"

def main(persist_dir: str, urls_file: str|None, pdf_dir: str|None):
    os.makedirs(persist_dir, exist_ok=True)
    client = chromadb.PersistentClient(path=persist_dir, settings=Settings(allow_reset=True))
    col = client.get_or_create_collection("docs")
    encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    docs, metadatas, ids = [], [], []

    if urls_file and os.path.exists(urls_file):
        with open(urls_file, "r", encoding="utf-8") as f:
            for url in f:
                url = url.strip()
                if not url: continue
                txt = read_url(url)
                if txt.startswith("[error]"):
                    print(txt); continue
                for ch in chunk_text(txt):
                    docs.append(ch)
                    metadatas.append({"source": url, "kind": "url"})
                    ids.append(str(uuid.uuid4()))

    if pdf_dir and os.path.isdir(pdf_dir):
        for name in os.listdir(pdf_dir):
            if not name.lower().endswith(".pdf"): continue
            path = os.path.join(pdf_dir, name)
            txt = read_pdf(path)
            if txt.startswith("[error]"):
                print(txt); continue
            for ch in chunk_text(txt):
                docs.append(ch)
                metadatas.append({"source": name, "kind": "pdf"})
                ids.append(str(uuid.uuid4()))

    if not docs:
        print("No documents found. You can still run the agent (it will use tools).")
        return

    print(f"Ingesting {len(docs)} chunks...")
    emb = encoder.encode(docs, normalize_embeddings=True).tolist()
    col.add(documents=docs, metadatas=metadatas, ids=ids, embeddings=emb)
    print("Done. Persisted to", persist_dir)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--persist_dir", default="./db")
    ap.add_argument("--urls", default="domain/demo/seed_urls.txt")
    ap.add_argument("--pdf_dir", default="domain/demo/seed_pdfs")
    args = ap.parse_args()
    main(args.persist_dir, args.urls, args.pdf_dir)
