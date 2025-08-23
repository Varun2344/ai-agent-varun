
import wikipedia

def search_wiki(query: str, max_pages: int = 2) -> str:
    try:
        titles = wikipedia.search(query)[:max_pages]
    except Exception as e:
        return f"[error] wiki search failed: {e}"
    out = []
    for t in titles:
        try:
            s = wikipedia.summary(t, auto_suggest=False)
            out.append(f"# {t}\n{s}")
        except Exception:
            pass
    return "\n\n---\n\n".join(out) if out else "No wiki results."
