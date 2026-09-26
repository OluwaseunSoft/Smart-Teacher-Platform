from __future__ import annotations

import math
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.llm import LLMError, get_embedder
from app.models import Chunk
from app.services.ai_usage import track_ai

Vector = Sequence[float]


def cosine(a: Vector, b: Vector) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def retrieve(
    db: Session,
    material_id: int,
    query: str,
    k: int | None = None,
    *,
    user_id: int | None = None,
) -> list[str]:
    """Return the top-k chunk texts for a material, most relevant first.

    Falls back to lexical overlap if embeddings are unavailable.
    Pure-Python similarity; fine at MVP scale (see docs/01-architecture.md).
    """
    return [
        c.content
        for c, _ in rank_chunks(db, material_id, query, k, user_id=user_id)
    ]


def rank_chunks(
    db: Session,
    material_id: int,
    query: str,
    k: int | None = None,
    *,
    user_id: int | None = None,
) -> list[tuple[Chunk, float]]:
    """Return the top-k ``(chunk, relevance)`` pairs, most relevant first.

    Relevance is normalised to ``[0, 1]`` so it can be persisted on
    ``TopicChunk.relevance``. Embeddings are used when present, otherwise a
    lexical overlap score is used. When an embedding lookup happens and ``db`` is
    available it is recorded in ``ai_usage_logs`` (operation ``retrieval.embed``);
    the row is persisted on the caller's next commit (best-effort).
    """
    k = k or settings.RETRIEVAL_TOP_K
    chunks = list(
        db.scalars(
            select(Chunk)
            .where(Chunk.material_id == material_id)
            .order_by(Chunk.index)
        )
    )
    if not chunks:
        return []

    embedded = [c for c in chunks if c.embedding]
    if embedded:
        try:
            embedder = get_embedder()
            with track_ai(db, embedder, "retrieval.embed", user_id=user_id):
                query_vec = embedder.embed([query])[0]
        except (LLMError, IndexError):
            query_vec = None

        if query_vec is not None:
            ranked = sorted(
                (
                    (c, max(0.0, cosine(c.embedding or [], query_vec)))
                    for c in embedded
                ),
                key=lambda pair: pair[1],
                reverse=True,
            )
            return ranked[:k]

    return _lexical_ranked(chunks, query, k)


def _lexical(chunks: list[Chunk], query: str, k: int) -> list[str]:
    return [c.content for c, _ in _lexical_ranked(chunks, query, k)]


def _lexical_ranked(
    chunks: list[Chunk], query: str, k: int
) -> list[tuple[Chunk, float]]:
    terms = {t for t in query.lower().split() if len(t) > 2}
    scored: list[tuple[int, int, Chunk]] = []
    for c in chunks:
        text = c.content.lower()
        score = sum(text.count(t) for t in terms)
        scored.append((score, -c.index, c))
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)

    top = scored[:k]
    peak = max((s for s, _, _ in top), default=0) or 1
    return [(c, s / peak) for s, _, c in top]
