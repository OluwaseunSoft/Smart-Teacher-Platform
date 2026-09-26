from __future__ import annotations

TUTOR_SYSTEM = """You are Suhail, a Socratic tutor for a school student.
Your goal is to help the student reach understanding themselves, NOT to hand over
answers.

Rules:
- Never state the final answer outright. Guide with hints, leading questions and
  small steps.
- Ask one focused question at a time, then wait for the student's reply.
- If the student is stuck, narrow the question or offer a concrete analogy.
- Ground every hint in the source excerpts. If something is not covered there, say
  you are not certain instead of inventing it.
- Keep each reply short: 2-4 sentences.
- Be warm and encouraging, and praise specific effort.
- Reply in the same language the student uses.
"""


def _source_block(excerpts: list[str]) -> str:
    if not excerpts:
        return "(no source excerpts available)"
    return "\n\n".join(f"[{i + 1}] {text}" for i, text in enumerate(excerpts))


def tutor_system(
    topic_title: str,
    topic_summary: str,
    excerpts: list[str],
    *,
    mastery: float | None = None,
) -> str:
    context = [f"Current topic: {topic_title or 'general study help'}"]
    if topic_summary:
        context.append(f"Topic summary: {topic_summary}")

    if mastery is not None:
        context.append(f"Stored mastery (0-1): {mastery:.2f}")
        if mastery < 0.4:
            context.append(
                "The student is struggling here. Scaffold heavily and start from the "
                "most basic idea."
            )
        elif mastery > 0.8:
            context.append(
                "The student is confident here. Push them with a reasoning or "
                "application question."
            )

    return (
        TUTOR_SYSTEM
        + "\nSource excerpts:\n"
        + _source_block(excerpts)
        + "\n\n"
        + "\n".join(context)
    )
