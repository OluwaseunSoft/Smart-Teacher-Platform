from __future__ import annotations

import io
import re
from contextlib import nullcontext

from sqlalchemy.orm import Session

from app.llm import LLMError, get_embedder
from app.models import Chunk
from app.services.ai_usage import track_ai

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
_WS = re.compile(r"[ \t]+")


def extract_pdf(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise ValueError("pypdf is required to read PDFs.") from exc

    reader = PdfReader(io.BytesIO(data))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)


def normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _WS.sub(" ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str) -> list[str]:
    """Split into overlapping chunks, preferring sentence boundaries."""
    text = normalize(text)
    if not text:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= CHUNK_SIZE:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)
            if len(sentence) > CHUNK_SIZE:
                for i in range(0, len(sentence), CHUNK_SIZE - CHUNK_OVERLAP):
                    chunks.append(sentence[i : i + CHUNK_SIZE])
                current = ""
            else:
                current = sentence

    if current:
        chunks.append(current)

    if CHUNK_OVERLAP and len(chunks) > 1:
        merged: list[str] = []
        for i, chunk in enumerate(chunks):
            if i == 0:
                merged.append(chunk)
                continue
            tail = chunks[i - 1][-CHUNK_OVERLAP:]
            merged.append(f"{tail} {chunk}".strip())
        chunks = merged

    return chunks


def ingest(
    text: str, *, db: Session | None = None, user_id: int | None = None
) -> list[Chunk]:
    """Chunk + embed text. Embedding failures degrade gracefully.

    When ``db`` is supplied the embedding call is recorded in ``ai_usage_logs``
    (operation ``ingestion.embed``) and committed immediately, since ingestion does
    not otherwise commit.
    """
    texts = chunk_text(text)
    if not texts:
        return []

    embeddings: list[list[float] | None] = [None] * len(texts)
    try:
        embedder = get_embedder()
        tracker = (
            track_ai(
                db, embedder, "ingestion.embed", user_id=user_id, commit=True
            )
            if db is not None
            else nullcontext()
        )
        with tracker:
            vectors = embedder.embed(texts)
        if len(vectors) == len(texts):
            embeddings = list(vectors)
    except LLMError:
        pass  # keep None; retrieval falls back to lexical matching

    return [
        Chunk(index=i, content=content, embedding=embedding)
        for i, (content, embedding) in enumerate(zip(texts, embeddings))
    ]
