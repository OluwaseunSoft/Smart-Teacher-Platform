from __future__ import annotations

ADAPTIVE_SYSTEM = """You are an encouraging personal teacher.
Write ONE short sentence (max 20 words) telling the student what happens next.
Do not ask questions. Do not include quotes.
"""


def adaptive_user(action: str, concept_title: str) -> str:
    return (
        f"Action: {action}. Concept: {concept_title}. "
        "Write a brief, motivating sentence."
    )
