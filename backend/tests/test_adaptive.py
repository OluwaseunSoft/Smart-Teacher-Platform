from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.models import (
    Chapter,
    Concept,
    Lesson,
    Mastery,
    Material,
    Question,
    Student,
    StudySession,
    Subject,
    Topic,
)
from app.services import adaptive


def _material(db, student, title="M"):
    material = Material(student_id=student.id, title=title, raw_text="x", status="ready")
    db.add(material)
    db.commit()
    return material


def _concept(db, material, subject, chapter, title, order):
    concept = Concept(material_id=material.id, title=title, order_index=order)
    db.add(concept)
    db.commit()
    topic = Topic(
        chapter_id=chapter.id, concept_id=concept.id, title=title, order_index=order
    )
    db.add(topic)
    db.commit()
    return concept, topic


def _session(db, student, material):
    session = StudySession(student_id=student.id, material_id=material.id)
    db.add(session)
    db.commit()
    return session


@pytest.fixture(autouse=True)
def _silence_message(monkeypatch):
    monkeypatch.setattr(adaptive, "_message", lambda *a, **k: "msg")


@pytest.fixture()
def world(db_session):
    student = Student(name="T")
    db_session.add(student)
    db_session.commit()

    material = _material(db_session, student)
    subject = Subject(material_id=material.id, name="Biology", order_index=0)
    db_session.add(subject)
    db_session.commit()
    chapter = Chapter(subject_id=subject.id, title="Cells", order_index=0)
    db_session.add(chapter)
    db_session.commit()

    concepts = []
    topics = []
    for i, title in enumerate(["Alpha", "Beta", "Gamma"]):
        concept, topic = _concept(db_session, material, subject, chapter, title, i)
        concepts.append(concept)
        topics.append(topic)

    session = _session(db_session, student, material)
    return SimpleNamespace(
        student=student,
        material=material,
        concepts=concepts,
        topics=topics,
        session=session,
    )


def _set_mastery(db, student, concept, score):
    db.add(
        Mastery(
            student_id=student.id,
            concept_id=concept.id,
            score=score,
            attempts=1,
            correct=1 if score > 0.5 else 0,
        )
    )
    db.commit()


def _make_lesson(db, material, concept, topic, *, simpler=False):
    lesson = Lesson(
        material_id=material.id,
        concept_id=concept.id,
        topic_id=topic.id,
        title=f"Lesson {concept.title}",
        content="body",
        status="ready",
        simpler=simpler,
    )
    db.add(lesson)
    db.commit()
    return lesson


def test_next_action_complete_without_concepts(db_session):
    student = Student(name="T")
    db_session.add(student)
    db_session.commit()
    material = _material(db_session, student, title="Empty")
    session = _session(db_session, student, material)

    result = adaptive.next_action(db_session, session)

    assert result["type"] == "complete"


def test_next_action_complete_when_material_missing(db_session):
    student = Student(name="T")
    db_session.add(student)
    db_session.commit()
    session = StudySession(student_id=student.id, material_id=99999)
    db_session.add(session)
    db_session.commit()

    result = adaptive.next_action(db_session, session)

    assert result["type"] == "complete"


def test_next_action_advances_to_first_topic(db_session, world):
    lesson = _make_lesson(
        db_session, world.material, world.concepts[0], world.topics[0]
    )

    result = adaptive.next_action(db_session, world.session)

    assert result["type"] == "advance"
    assert result["concept"].id == world.concepts[0].id
    assert result["lesson"].id == lesson.id
    db_session.refresh(world.session)
    assert world.session.current_concept_id == world.concepts[0].id


def test_next_action_advance_skips_mastered_topics(db_session, world):
    for i, concept in enumerate(world.concepts):
        _set_mastery(db_session, world.student, concept, 0.5 if i == 1 else 0.9)
    world.session.current_concept_id = world.concepts[0].id
    db_session.commit()

    result = adaptive.next_action(db_session, world.session)

    assert result["type"] == "advance"
    assert result["concept"].id == world.concepts[1].id


def test_next_action_reteach_when_weak(db_session, world):
    concept, topic = world.concepts[0], world.topics[0]
    _set_mastery(db_session, world.student, concept, 0.1)
    simple = _make_lesson(db_session, world.material, concept, topic, simpler=True)
    world.session.current_concept_id = concept.id
    db_session.commit()

    result = adaptive.next_action(db_session, world.session)

    assert result["type"] == "reteach"
    assert result["concept"].id == concept.id
    assert result["lesson"].id == simple.id
    assert result["lesson"].simpler is True


def test_next_action_practice_when_midway(db_session, world):
    concept, topic = world.concepts[0], world.topics[0]
    _set_mastery(db_session, world.student, concept, 0.5)
    lesson = _make_lesson(db_session, world.material, concept, topic)
    question = Question(
        lesson_id=lesson.id,
        concept_id=concept.id,
        type="mcq",
        prompt="Which one?",
        options=["A", "B"],
        answer="A",
        difficulty=2,
    )
    db_session.add(question)
    db_session.commit()
    world.session.current_concept_id = concept.id
    db_session.commit()

    result = adaptive.next_action(db_session, world.session)

    assert result["type"] == "practice"
    assert result["quiz"]["lesson_id"] == lesson.id
    assert len(result["quiz"]["questions"]) == 1
    assert result["quiz"]["questions"][0]["id"] == question.id


def test_next_action_completes_when_all_mastered(db_session, world):
    for concept in world.concepts:
        _set_mastery(db_session, world.student, concept, 0.9)

    result = adaptive.next_action(db_session, world.session)

    assert result["type"] == "complete"
    db_session.refresh(world.session)
    assert world.session.status == "completed"
