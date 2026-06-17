"""
qa_chain.py
Builds a ConversationalRetrievalChain powered by Groq (llama-3.1-8b-instant)
with LangChain ConversationBufferMemory for multi-turn context.
"""
from __future__ import annotations
import os
from typing import Dict, Any

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_groq import ChatGroq

from src.vector_store import VectorStore


_DEFAULT_MODEL = "llama-3.1-8b-instant"   # fast & free on Groq


class QAChain:
    def __init__(self, vector_store: VectorStore, top_k: int = 4, model: str = _DEFAULT_MODEL):
        self._memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer",
        )
        llm = ChatGroq(
    model_name=model,
    temperature=0.2,
    max_tokens=1024,
)
        retriever = vector_store.as_retriever(k=top_k)

        self._chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=retriever,
            memory=self._memory,
            return_source_documents=True,
            verbose=False,
        )

    # ── Public ────────────────────────────────────────────────────────────────
    def ask(self, question: str) -> Dict[str, Any]:
        """Run the chain and return the full result dict (answer + source_documents)."""
        result = self._chain({"question": question})
        return result

    def clear_memory(self) -> None:
        self._memory.clear()
