import nltk
nltk.download("punkt")
nltk.download("punkt_tab")

from nltk.tokenize import sent_tokenize

MAX_TOKENS = 256
OVERLAP = 40

def chunk_text(text: str):
    sentences = sent_tokenize(text)
    chunks = []
    current = []

    tokens = 0
    for sent in sentences:
        length = len(sent.split())
        if tokens + length > MAX_TOKENS:
            chunks.append(" ".join(current))
            current = current[-OVERLAP:]
            tokens = sum(len(s.split()) for s in current)

        current.append(sent)
        tokens += length

    if current:
        chunks.append(" ".join(current))

    return chunks
