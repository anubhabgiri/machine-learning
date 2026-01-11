from duckduckgo_search import DDGS
from chunking import chunk_text

def web_search(query: str, max_results=5):
    docs = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            docs.append(r["body"])

    chunks = []
    for d in docs:
        chunks.extend(chunk_text(d))

    return chunks
