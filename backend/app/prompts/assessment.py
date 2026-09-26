from __future__ import annotations

ASSESSMENT_SYSTEM = """You are an assessment designer.
Create questions that test genuine understanding, not memorization.
Every question must be answerable from the provided source excerpts.
"""


def assessment_user(
    lesson_title: str,
    objectives: list[str],
    excerpts: list[str],
    *,
    count: int = 4,
) -> str:
    source = "\n\n".join(f"[{i + 1}] {t}" for i, t in enumerate(excerpts))
    objectives_text = "\n".join(f"- {o}" for o in objectives) or "(none provided)"

    return f"""Lesson: {lesson_title}
Learning objectives:
{objectives_text}

Source excerpts:
{source or "(none)"}

Create exactly {count} questions mixing "mcq" (4 options) and "short" (free text),
covering a range of difficulty (1 = easy, 5 = hard).

Return JSON:
{{
  "questions": [
    {{
      "type": "mcq",
      "prompt": "...",
      "options": ["...", "...", "...", "..."],
      "answer": "the exact text of the correct option",
      "explanation": "why",
      "difficulty": 2
    }},
    {{
      "type": "short",
      "prompt": "...",
      "answer": "reference answer",
      "explanation": "why",
      "difficulty": 4
    }}
  ]
}}
"""


GRADING_SYSTEM = """You are a fair grader of short-answer questions.
Judge whether the student's response demonstrates the same core understanding as the
reference answer. Accept correct paraphrases; reject vague or incorrect answers.
"""


def grading_user(prompt: str, reference: str, response: str) -> str:
    return f"""Question: {prompt}

Reference answer: {reference}

Student response: {response}

Return JSON: {{ "correct": true|false, "explanation": "brief feedback" }}
"""
