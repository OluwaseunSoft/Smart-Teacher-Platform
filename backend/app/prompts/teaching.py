from __future__ import annotations

TEACHING_SYSTEM = """You are a patient, expert personal teacher.
Ground every claim in the provided source excerpts. If a detail is not in the
sources, do not assert it as fact.
Write in plain language, short paragraphs, with concrete examples and analogies.
Output GitHub-flavored markdown with headings.
"""


def teaching_user(
    concept_title: str,
    concept_summary: str,
    excerpts: list[str],
    *,
    simpler: bool = False,
) -> str:
    source = "\n\n".join(
        f"[{i + 1}] {text}" for i, text in enumerate(excerpts)
    ) or "(no source excerpts available)"

    style = (
        "The student struggled with this concept. Explain it SIMPLER: use shorter "
        "sentences, more everyday analogies, and take smaller steps. Assume no prior "
        "knowledge of the jargon."
        if simpler
        else "Teach at an appropriate depth for the concept's difficulty."
    )

    return f"""Concept: {concept_title}
Summary: {concept_summary}

Source excerpts:
{source}

{style}

Produce a lesson in JSON with this exact shape:
{{
  "title": "lesson title",
  "objectives": ["objective 1", "objective 2", "objective 3"],
  "content_markdown": "## Why this matters\\n...\\n## Core idea\\n...\\n## Worked example\\n...\\n## Common misconception\\n...\\n## Summary\\n- ..."
}}
"""
