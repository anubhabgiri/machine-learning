import faiss
import numpy as np
from models import embedding_model

class Retriever:
    def __init__(self, chunks: list[str]):
        self.chunks = chunks
        self.embeddings = embedding_model.encode(chunks)
        self.index = faiss.IndexFlatL2(self.embeddings.shape[1])
        self.index.add(self.embeddings)

    def retrieve(self, query: str, k=4):
        q_emb = embedding_model.encode([query])
        _, idxs = self.index.search(np.array(q_emb), k)
        return [self.chunks[i] for i in idxs[0]]
