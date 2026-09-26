from __future__ import annotations

from app.services.adaptive import update_mastery
from app.services.assessment import _normalize
from app.services.ingestion import chunk_text, normalize
from app.services.retrieval import _lexical
from app.models import Chunk


def test_normalize_collapses_whitespace():
    assert normalize("a   b\r\n\r\n\r\nc") == "a b\n\nc"


def test_chunk_text_respects_size_and_overlap():
    text = ". ".join(f"Sentence number {i}" for i in range(200)) + "."
    chunks = chunk_text(text)
    assert len(chunks) > 1
    assert all(len(c) <= 1100 for c in chunks)


def test_lexical_ranks_by_term_overlap():
    chunks = [
        Chunk(index=0, content="photosynthesis light reactions"),
        Chunk(index=1, content="mitosis cell division"),
        Chunk(index=2, content="photosynthesis calvin cycle"),
    ]
    top = _lexical(chunks, "photosynthesis", 2)
    assert len(top) == 2
    assert all("photosynthesis" in c for c in top)


def test_normalize_answer_strips_punctuation_and_case():
    assert _normalize("  The Nucleus. ") == "the nucleus"


def test_mastery_increases_after_correct(db_session):
    from app.models import Concept, Material, Student

    student = Student(name="T")
    material = Material(student_id=1, title="M", raw_text="x")
    db_session.add_all([student, material])
    db_session.commit()

    concept = Concept(material_id=material.id, title="C", order_index=0)
    db_session.add(concept)
    db_session.commit()

    record = update_mastery(db_session, student.id, concept.id, True, 3)
    assert record.attempts == 1
    assert record.correct == 1
    assert 0.0 < record.score <= 1.0
    first_score = record.score

    record2 = update_mastery(db_session, student.id, concept.id, False, 3)
    assert record2.attempts == 2
    assert record2.score < first_score
