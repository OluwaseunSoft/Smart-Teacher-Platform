from __future__ import annotations

STRUCTURING_SYSTEM = """You are an expert curriculum designer.
You decompose study material into a clean, ordered curriculum of teachable concepts.
Rules:
- Produce between 5 and 15 top-level concepts, in a sensible learning order.
- Each concept needs a concise title, a one-paragraph summary, and a difficulty
  from exactly one of: "intro", "core", "advanced".
- Decompose broad concepts into at most 4 "subconcepts" when useful.
- Base everything ONLY on the provided material. Do not invent topics.
"""


def structuring_user(title: str, outline: str) -> str:
    return f"""Material title: {title}

Content (may be an outline or excerpts):
\"\"\"
{outline}
\"\"\"

Return JSON with this exact shape:
{{
  "title": "overall curriculum title",
  "concepts": [
    {{
      "title": "...",
      "summary": "...",
      "difficulty": "intro|core|advanced",
      "subconcepts": [ {{ "title": "...", "summary": "..." }} ]
    }}
  ]
}}
"""
