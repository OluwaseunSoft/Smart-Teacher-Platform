from __future__ import annotations

from sqlalchemy import select

from app.llm import LLMError
from app.models import (
    AIUsageLog,
    Chapter,
    Chunk,
    Concept,
    Lesson,
    Material,
    Question,
    Student,
    Subject,
    Topic,
)
from app.services import assessment, structuring
from app.services import ingestion, retrieval
from app.services import tutor as tutor_service

PASSWORD = "password123"


def _signup(client, email="student@example.com", name="Student"):
    return client.post(
        "/api/auth/signup",
        json={"email": email, "password": PASSWORD, "display_name": name},
    )


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _material(client, token, title="Biology"):
    resp = client.post(
        "/api/materials/text",
        json={"title": title, "text": "Cells are the basic unit of life."},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _topic(session, material_id, title="Nucleus"):
    subject = Subject(material_id=material_id, name="Biology", order_index=0)
    session.add(subject)
    session.commit()
    chapter = Chapter(subject_id=subject.id, title="Cells", order_index=0)
    session.add(chapter)
    session.commit()
    topic = Topic(chapter_id=chapter.id, title=title, order_index=0)
    session.add(topic)
    session.commit()
    return topic


class _UsageLLM:
    name = "fake"
    model = "fake-1"
    last_usage = {"prompt_tokens": 11, "completion_tokens": 7}

    def __init__(self, result=None, reply="What do you already know?"):
        self.result = result or {}
        self.reply = reply

    def generate_json(self, messages, system=None, **kwargs):  # noqa: ANN001
        return self.result

    def complete(self, messages, *, system=None, temperature=0.3, max_tokens=2048):
        return self.reply

    def embed(self, texts):
        return [[0.0] for _ in texts]


class _FailingLLM:
    name = "fake"
    model = "fake-1"

    def complete(self, messages, *, system=None, temperature=0.3, max_tokens=2048):
        raise LLMError("provider down")

    def generate_json(self, messages, system=None, **kwargs):  # noqa: ANN001
        raise LLMError("provider down")

    def embed(self, texts):
        return [[0.0] for _ in texts]


class _Embedder:
    name = "fake-embed"
    model = "fake-gen"
    last_model = "fake-embed-model"
    last_usage = {"prompt_tokens": 21, "completion_tokens": 0}

    def __init__(self, *, error: Exception | None = None):
        self.error = error
        self.calls = 0

    def embed(self, texts):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return [[0.1, 0.2] for _ in texts]


def _latest(session) -> AIUsageLog:
    row = session.scalar(select(AIUsageLog).order_by(AIUsageLog.id.desc()))
    assert row is not None
    return row


def test_ingestion_embedding_is_logged(db_session, monkeypatch):
    embedder = _Embedder()
    monkeypatch.setattr(ingestion, "get_embedder", lambda: embedder)

    chunks = ingestion.ingest(
        "Cells are the basic unit of life. " * 40, db=db_session, user_id=7
    )

    assert chunks and chunks[0].embedding == [0.1, 0.2]
    assert embedder.calls == 1
    row = _latest(db_session)
    assert row.operation == "ingestion.embed"
    assert row.provider == "fake-embed"
    assert row.model == "fake-embed-model"
    assert row.user_id == 7
    assert row.prompt_tokens == 21
    assert row.status == "ok"


def test_ingestion_embedding_failure_degrades_and_logs_error(db_session, monkeypatch):
    embedder = _Embedder(error=LLMError("no embeddings"))
    monkeypatch.setattr(ingestion, "get_embedder", lambda: embedder)

    chunks = ingestion.ingest("Some study notes.", db=db_session)

    assert chunks and chunks[0].embedding is None
    row = _latest(db_session)
    assert row.operation == "ingestion.embed"
    assert row.status == "error"
    assert row.error is not None and "no embeddings" in row.error


def test_retrieval_embedding_is_logged(db_session, monkeypatch):
    student = Student(name="T")
    material = Material(student_id=1, title="M", raw_text="x")
    db_session.add_all([student, material])
    db_session.commit()
    db_session.add(
        Chunk(material_id=material.id, index=0, content="cells", embedding=[1.0, 0.0])
    )
    db_session.commit()

    embedder = _Embedder()
    monkeypatch.setattr(retrieval, "get_embedder", lambda: embedder)

    ranked = retrieval.rank_chunks(
        db_session, material.id, "cell", user_id=3
    )

    assert ranked and embedder.calls == 1
    db_session.commit()
    row = _latest(db_session)
    assert row.operation == "retrieval.embed"
    assert row.model == "fake-embed-model"
    assert row.user_id == 3
    assert row.status == "ok"



def test_structuring_call_is_logged(db_session, monkeypatch):
    monkeypatch.setattr(structuring, "get_llm", lambda: _UsageLLM(result={"concepts": []}))

    student = Student(name="T")
    material = Material(student_id=1, title="M", raw_text="cell biology content")
    db_session.add_all([student, material])
    db_session.commit()

    structuring.build_curriculum(db_session, material)

    row = _latest(db_session)
    assert row.operation == "structuring"
    assert row.provider == "fake"
    assert row.model == "fake-1"
    assert row.prompt_tokens == 11
    assert row.completion_tokens == 7
    assert row.status == "ok"
    assert row.latency_ms >= 0


def test_tutor_reply_is_logged_with_user(api_client, test_session, monkeypatch):
    fake = _UsageLLM()
    monkeypatch.setattr(tutor_service, "get_llm", lambda: fake)

    token = _signup(api_client).json()["access_token"]
    user_id = api_client.get("/api/auth/me", headers=_auth(token)).json()["id"]
    material_id = _material(api_client, token)
    topic = _topic(test_session, material_id)
    test_session.add(Chunk(material_id=material_id, index=0, content="DNA"))
    test_session.commit()

    conversation_id = api_client.post(
        "/api/tutor/conversations",
        json={"topic_id": topic.id},
        headers=_auth(token),
    ).json()["id"]
    resp = api_client.post(
        f"/api/tutor/conversations/{conversation_id}/messages",
        json={"content": "What is the nucleus?"},
        headers=_auth(token),
    )
    assert resp.status_code == 200

    row = _latest(test_session)
    assert row.operation == "tutor.reply"
    assert row.user_id == user_id
    assert row.status == "ok"
    assert row.prompt_tokens == 11


def test_grading_call_is_logged(api_client, test_session, monkeypatch):
    fake = _UsageLLM(result={"correct": True, "explanation": "yes"})
    monkeypatch.setattr(assessment, "get_llm", lambda: fake)

    token = _signup(api_client).json()["access_token"]
    material_id = _material(api_client, token)

    subject = Subject(material_id=material_id, name="Biology")
    test_session.add(subject)
    test_session.commit()
    chapter = Chapter(subject_id=subject.id, title="Cells")
    test_session.add(chapter)
    test_session.commit()
    concept = Concept(material_id=material_id, title="Nucleus")
    test_session.add(concept)
    test_session.commit()
    lesson = Lesson(
        material_id=material_id,
        concept_id=concept.id,
        title="Lesson",
        content="content",
        status="ready",
    )
    test_session.add(lesson)
    test_session.commit()
    question = Question(
        lesson_id=lesson.id,
        concept_id=concept.id,
        type="short",
        prompt="Explain the nucleus.",
        answer="Control center",
        explanation="It stores DNA.",
        difficulty=2,
    )
    test_session.add(question)
    test_session.commit()

    resp = api_client.post(
        f"/api/quizzes/{lesson.id}/submit",
        json={"answers": [{"question_id": question.id, "response": "control center"}]},
        headers=_auth(token),
    )
    assert resp.status_code == 200

    row = _latest(test_session)
    assert row.operation == "assessment.grade"
    assert row.status == "ok"


def test_failed_call_logs_error(api_client, test_session, monkeypatch):
    monkeypatch.setattr(tutor_service, "get_llm", lambda: _FailingLLM())

    token = _signup(api_client).json()["access_token"]
    material_id = _material(api_client, token)
    topic = _topic(test_session, material_id)

    conversation_id = api_client.post(
        "/api/tutor/conversations",
        json={"topic_id": topic.id},
        headers=_auth(token),
    ).json()["id"]
    resp = api_client.post(
        f"/api/tutor/conversations/{conversation_id}/messages",
        json={"content": "Hello"},
        headers=_auth(token),
    )
    assert resp.status_code == 502

    row = _latest(test_session)
    assert row.operation == "tutor.reply"
    assert row.status == "error"
    assert row.error is not None and "provider down" in row.error
