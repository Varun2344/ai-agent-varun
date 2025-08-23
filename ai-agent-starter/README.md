
# Domain-Aware AI Agent (Free, Local)

A simple, free, **hackathon-ready** AI agent that:
- reads your domain docs (PDFs/URLs)
- stores them locally with embeddings
- retrieves relevant chunks (RAG)
- uses a local LLM via **Ollama** (no paid APIs)
- can call simple **tools** (Wikipedia, web fetch, calculator)
- shows sources for trust
- has a small **Gradio** UI

---

## 1) Prereqs

- Install **Python 3.10+**
- Install **Ollama** (https://ollama.com/) and pull a small model:
  ```bash
  ollama pull mistral:7b
  # optional alternatives:
  # ollama pull llama3.1:8b
  # ollama pull tinyllama
  ```

## 2) Setup

```bash
# clone or unzip this project, then:
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

## 3) Ingest docs (build local knowledge base)

Put your PDFs into `domain/demo/seed_pdfs/` (optional), and add URLs to `domain/demo/seed_urls.txt`.

Then run:
```bash
python -m rag.ingest --persist_dir ./db --urls domain/demo/seed_urls.txt --pdf_dir domain/demo/seed_pdfs
```

## 4) Run the app

```bash
python app.py
```
Open the link shown in the terminal. Ask something like:
> What is Retrieval-Augmented Generation (RAG)? Cite sources.

Tip: To create a temporary public link for judging, set `share=True` in `app.py`'s `demo.launch()`.

---

## Project Structure

```
ai-agent-starter/
├─ app.py                 # Gradio UI
├─ agent.py               # Simple agent loop (local LLM + tools + RAG)
├─ rag/
│  ├─ ingest.py           # PDFs/URLs → chunks → embeddings → Chroma
│  └─ utils.py            # clean & chunk helpers
├─ tools/
│  ├─ wiki.py             # Wikipedia summaries
│  ├─ web.py              # Fetch a webpage (text only)
│  └─ calc.py             # Basic arithmetic
├─ domain/
│  └─ demo/
│     ├─ seed_urls.txt
│     └─ seed_pdfs/       # put PDFs here
├─ tests/
│  └─ test_agent.py       # basic smoke tests
├─ requirements.txt
├─ .gitignore
└─ README.md
```

---

## Notes
- 100% free; no paid APIs.
- If your laptop is slow, prefer `mistral:7b` or `tinyllama` and keep documents small.
- This is a starter; extend tools, add guardrails, or switch UI to Streamlit as needed.
