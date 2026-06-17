"""
vector_store.py
Builds and queries a FAISS index using HuggingFace sentence-transformers embeddings.
Everything runs locally — no external vector DB needed.
"""
from __future__ import annotations
from typing import List

from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings


_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"   # ~90 MB, runs on CPU


class VectorStore:
    def __init__(self, model_name: str = _EMBED_MODEL):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        self._store: FAISS | None = None

    # ── Build ─────────────────────────────────────────────────────────────────
    def build(self, documents: List[Document]) -> None:
        """Create a FAISS index from a list of Documents."""
        self._store = FAISS.from_documents(documents, self.embeddings)

    # ── Retriever ─────────────────────────────────────────────────────────────
    def as_retriever(self, k: int = 4):
        if self._store is None:
            raise RuntimeError("VectorStore not built. Call build() first.")
        return self._store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k},
        )

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        if self._store is None:
            raise RuntimeError("VectorStore not built.")
        return self._store.similarity_search(query, k=k)

    # ── Persistence (optional) ─────────────────────────────────────────────────
    def save(self, path: str) -> None:
        if self._store:
            self._store.save_local(path)

    def load(self, path: str) -> None:
        self._store = FAISS.load_local(path, self.embeddings, allow_dangerous_deserialization=True)
