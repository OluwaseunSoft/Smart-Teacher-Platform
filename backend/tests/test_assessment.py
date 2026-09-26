from __future__ import annotations

import pytest

from app.models import Concept, Lesson, Material, Question, Student
from app.services import assessment


class FakeProvider:
    name = "fake"
    model = "fake-model"

    def __init__(self, data=None, *, error: Exception | None = None):
        self.data = data
        self.error = error
        self.calls: list[tuple] = []

    def generate_json(self, messages, **kwargs):
        self.calls.append((messages, kwargs))
        if self.error is not None:
            raise self.error
        return self.data


def _question(**overrides) -> Question:
    defaults = dict(
        lesson_id=1,
        concept_id=1,
        type="mcq",
        prompt="Which structure stores DNA?",
        options=["Nucleus", "Membrane"],
        answer="Nucleus",
        explanation="The nucleus holds the DNA.",
        difficulty=2,
    )
    defaults.update(overrides)
    return Question(**defaults)


def test_mcq_grading_is_case_and_whitespace_insensitive():
    correct, explanation = assessment.grade_answer(_question(), "  NUCLEUS. ")
    assert correct is True
    assert explanation == "The nucleus holds the DNA."


def test_mcq_grading_accepts_option_letter():
    question = _question(options=["Membrane", "Nucleus"], answer="Nucleus")
    assert assessment.grade_answer(question, "B")[0] is True
    assert assessment.grade_answer(question, "b)")[0] is True
    assert assessment.grade_answer(question, "A")[0] is False


def test_mcq_grading_rejects_wrong_answer():
    correct, _ = assessment.grade_answer(_question(), "Membrane")
    assert correct is False


def test_grading_empty_response_is_incorrect():
    correct, explanation = assessment.grade_answer(_question(), "   ")
    assert correct is False
    assert explanation == "The nucleus holds the DNA."


def test_short_answer_grading_uses_provider(monkeypatch):
    provider = FakeProvider({"correct": True, "explanation": "Close enough."})
    monkeypatch.setattr(assessment, "get_llm", lambda: provider)
    question = _question(type="short", options=None, answer="mitochondria")

    correct, explanation = assessment.grade_answer(question, "the powerhouse")

    assert correct is True
    assert explanation == "Close enough."
    assert len(provider.calls) == 1


def test_short_answer_grading_falls_back_when_provider_misbehaves(monkeypatch):
    monkeypatch.setattr(assessment, "get_llm", lambda: FakeProvider(None))
    question = _question(type="short", options=None, answer="mitochondria")

    correct, explanation = assessment.grade_answer(question, "powerhouse")

    assert correct is False
    assert explanation == question.explanation


def test_difficulty_is_clamped():
    assert assessment._difficulty(0) == 1
    assert assessment._difficulty(9) == 5
    assert assessment._difficulty("3") == 3
    assert assessment._difficulty("nope") == 2


def _lesson(db) -> Lesson:
    student = Student(name="T")
    db.add(student)
    db.commit()
    material = Material(student_id=student.id, title="M", raw_text="x", status="ready")
    db.add(material)
    db.commit()
    concept = Concept(material_id=material.id, title="C", order_index=0)
    db.add(concept)
    db.commit()
    lesson = Lesson(
        material_id=material.id,
        concept_id=concept.id,
        title="Lesson",
        objectives=["learn"],
        content="body",
        status="ready",
    )
    db.add(lesson)
    db.commit()
    return lesson


def test_generate_quiz_returns_existing_without_calling_provider(db_session, monkeypatch):
    lesson = _lesson(db_session)
    existing = _question(lesson_id=lesson.id, concept_id=lesson.concept_id)
    db_session.add(existing)
    db_session.commit()

    provider = FakeProvider(error=AssertionError("LLM should not be called"))
    monkeypatch.setattr(assessment, "get_llm", lambda: provider)

    questions = assessment.generate_quiz(db_session, lesson)

    assert [q.id for q in questions] == [existing.id]
    assert provider.calls == []


def test_generate_quiz_normalizes_types_and_skips_invalid(db_session, monkeypatch):
    lesson = _lesson(db_session)
    monkeypatch.setattr(assessment, "retrieve", lambda *a, **k: [])
    provider = FakeProvider(
        {
            "questions": [
                {
                    "prompt": "Q1",
                    "type": "mcq",
                    "options": ["a", "b"],
                    "answer": "a",
                    "difficulty": 4,
                },
                {"prompt": "Q2", "type": "weird", "options": ["x"], "answer": "x"},
                {"prompt": "Q3", "type": "mcq", "options": [], "answer": "x"},
                {"no_prompt": True},
            ]
        }
    )
    monkeypatch.setattr(assessment, "get_llm", lambda: provider)

    questions = assessment.generate_quiz(db_session, lesson)

    assert [q.prompt for q in questions] == ["Q1", "Q2", "Q3"]
    assert [q.type for q in questions] == ["mcq", "mcq", "short"]
    assert questions[2].options is None
    assert questions[0].difficulty == 4
    assert len(provider.calls) == 1
