from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models import AIUsageLog, Concept, Lesson, Material, Student
from app.llm.base import LLMOutputTruncated
from app.services import teaching


VALID = {
    "title": "Arabic literature",
    "objectives": ["Identify literary periods"],
    "content_markdown": "## Literature\nA grounded lesson.",
}


@pytest.fixture()
def lesson_context(db_session, monkeypatch):
    student = Student(name="Student")
    db_session.add(student)
    db_session.flush()
    material = Material(student_id=student.id, title="Literature", raw_text="Source")
    db_session.add(material)
    db_session.flush()
    concept = Concept(material_id=material.id, title="Literature", order_index=0)
    db_session.add(concept)
    db_session.commit()
    monkeypatch.setattr(teaching, "rank_chunks", lambda *args, **kwargs: [])
    return material, concept


class Provider:
    name = "fake"
    model = "fake"

    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def generate_json(self, messages, **kwargs):
        self.calls.append(messages)
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response


def test_valid_lesson_needs_one_call(db_session, monkeypatch, lesson_context):
    provider = Provider([VALID])
    monkeypatch.setattr(teaching, "get_llm", lambda: provider)
    lesson = teaching.generate_lesson(db_session, *lesson_context)
    assert lesson.content == VALID["content_markdown"]
    assert lesson.objectives == VALID["objectives"]
    assert len(provider.calls) == 1


@pytest.mark.parametrize("invalid", [
    [VALID], None, "lesson", {},
    {**VALID, "objectives": "objective"},
    {**VALID, "content_markdown": "  "},
    {**VALID, "content_markdown": {"text": "lesson"}},
])
def test_invalid_lesson_is_repaired(db_session, monkeypatch, lesson_context, invalid):
    provider = Provider([invalid, VALID])
    monkeypatch.setattr(teaching, "get_llm", lambda: provider)
    lesson = teaching.generate_lesson(db_session, *lesson_context)
    assert lesson.content == VALID["content_markdown"]
    assert len(provider.calls) == 2
    assert provider.calls[1][-1]["role"] == "user"
    logs = list(db_session.scalars(select(AIUsageLog).order_by(AIUsageLog.id)))
    assert [log.status for log in logs] == ["error", "ok"]


def test_invalid_retry_does_not_save_lesson(db_session, monkeypatch, lesson_context):
    provider = Provider([[VALID], {}])
    monkeypatch.setattr(teaching, "get_llm", lambda: provider)
    with pytest.raises(ValueError, match="after two attempts"):
        teaching.generate_lesson(db_session, *lesson_context)
    assert db_session.scalar(select(Lesson)) is None
    assert len(provider.calls) == 2


def test_truncated_lesson_retries_with_larger_budget(db_session, monkeypatch, lesson_context):
    provider = Provider([LLMOutputTruncated("Output limit"), VALID])
    budgets = []
    generate = provider.generate_json

    def capture(messages, **kwargs):
        budgets.append(kwargs["max_tokens"])
        return generate(messages, **kwargs)

    monkeypatch.setattr(provider, "generate_json", capture)
    monkeypatch.setattr(teaching, "get_llm", lambda: provider)
    lesson = teaching.generate_lesson(db_session, *lesson_context)
    assert lesson.content == VALID["content_markdown"]
    assert budgets == [4096, 8192]
