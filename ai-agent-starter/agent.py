
import json
from typing import Dict, Any, List
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import ollama

from tools.wiki import search_wiki
from tools.web import fetch_url
from tools.calc import calculator

SYSTEM_HINT = """You are a helpful domain-aware assistant.
You may use ONE optional tool BEFORE answering:
- vector_search: search the local knowledge base
- wiki: search concise Wikipedia summaries
- web: fetch a web page by URL
- calc: do basic arithmetic

Return a JSON plan first:
{"tool": "vector_search" | "wiki" | "web" | "calc" | "none", "args": "...", "reason": "why"}

After we run the tool (if any), you will get the RESULTS and then you must produce a final, cited answer in markdown.
Keep answers concise, cite sources with titles/URLs when available.
"""

def call_llm(prompt: str, model: str = "mistral:7b") -> str:
    r = ollama.chat(model=model, messages=[{"role":"system","content":SYSTEM_HINT},
                                           {"role":"user","content":prompt}])
    return r["message"]["content"]

class Retriever:
    def __init__(self, persist_dir="./db"):
        self.client = chromadb.PersistentClient(path=persist_dir, settings=Settings(allow_reset=True))
        self.col = self.client.get_or_create_collection("docs")
        self.encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def search(self, query: str, k: int = 4):
        if self.col.count() == 0:
            return []
        q = self.encoder.encode([query], normalize_embeddings=True).tolist()[0]
        res = self.col.query(query_embeddings=[q], n_results=k, include=["documents","metadatas"])
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        items = []
        for d, m in zip(docs, metas):
            src = m.get("source","unknown")
            items.append({"text": d, "source": src})
        return items

def plan(query: str) -> Dict[str, str]:
    p = f"""User query: {query}

First, decide ONE tool that would help most (or "none"). Output ONLY the JSON, no extra text."""
    raw = call_llm(p)
    try:
        if "```json" in raw:
            raw = raw.split("```json",1)[1].split("```",1)[0]
        j = json.loads(raw)
        tool = j.get("tool","none")
        args = j.get("args","")
        reason = j.get("reason","")
        return {"tool": tool, "args": args, "reason": reason}
    except Exception:
        return {"tool":"none","args":"","reason":"parse-failed"}

def run(query: str, retriever: Retriever, model: str = "mistral:7b") -> Dict[str, Any]:
    decision = plan(query)
    tool_used = decision["tool"]
    result = ""
    sources = []

    if tool_used == "vector_search":
        hits = retriever.search(query, k=4)
        result = "\n\n".join([f"[{i+1}] ({h['source']})\n{h['text']}" for i,h in enumerate(hits)]) or "No local results."
        sources = list({h["source"] for h in hits})
    elif tool_used == "wiki":
        target = decision["args"] or query
        result = search_wiki(target)
    elif tool_used == "web":
        url = decision["args"]
        result = fetch_url(url) if url else "[error] No URL provided."
        sources = [url] if url else []
    elif tool_used == "calc":
        result = calculator(decision["args"])
    else:
        result = "(No tool used.)"

    final_prompt = f"""User question: {query}

Tool chosen: {tool_used}
Reason: {decision['reason']}
TOOL_RESULTS:
{result}

Now write the FINAL ANSWER in markdown, with a brief explanation and a bullet list of sources (if any)."""
    answer = call_llm(final_prompt, model=model)
    return {"tool": tool_used, "answer": answer, "sources": sources}

if __name__ == "__main__":
    r = Retriever("./db")
    out = run("Summarize the topic in our local knowledge and add 2 facts from Wikipedia about it.", r)
    print(out["answer"])
