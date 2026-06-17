"""
utils.py
Small helper functions for the Streamlit UI.
"""
from __future__ import annotations
from typing import List
from langchain.schema import Document


def format_source_info(source_docs: List[Document]) -> List[str]:
    """Return a deduplicated list of human-readable source labels."""
    seen = set()
    labels = []
    for doc in source_docs:
        meta = doc.metadata
        source = meta.get("source", "unknown")
        page = meta.get("page")
        row = meta.get("row")

        if page:
            label = f"{source} · p{page}"
        elif row:
            label = f"{source} · row {row}"
        else:
            label = source

        if label not in seen:
            seen.add(label)
            labels.append(label)
    return labels


def get_file_icon(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    icons = {"pdf": "📄", "txt": "📝", "docx": "📘", "csv": "📊"}
    return icons.get(ext, "📁")
