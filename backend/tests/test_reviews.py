from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models import (
    Chapter,
    Concept,
    Lesson,
    MasteryEvent,
    Question,
    ReviewSchedule,
    Student,
    Subject,
    Topic,
)

PASSWORD = "password123"


def _signup(client, email="student@example.com", name="Student"):
    return client.post(
        "/api/auth/signup",
        json={"email": email, "password": PASSWORD, "display_name": name},
    )


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _user_id(client, token: str) -> int:
    return client.get("/api/auth/me", headers=_auth(token)).json()["id"]


def _material(client, token, title="Biology"):
    resp = client.post(
        "/api/materials/text",
        json={"title": title, "text": "Cells are the basic unit of life."},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _curriculum(session, material_id, title="Nucleus"):
    subject = Subject(material_id=material_id, name="Biology", order_index=0)
    session.add(subject)
    session.commit()
    chapter = Chapter(subject_id=subject.id, title="Cells", order_index=0)
    session.add(chapter)
    session.commit()
    concept = Concept(material_id=material_id, title=title, order_index=0)
    session.add(concept)
    session.commit()
    topic = Topic(
        chapter_id=chapter.id, concept_id=concept.id, title=title, order_index=0
    )
    session.add(topic)
    session.commit()
    return topic, concept


def test_submit_review_creates_schedule(api_client, test_session):
    token = _signup(api_client).json()["access_token"]
    material_id = _material(api_client, token)
    topic, _ = _curriculum(test_session, material_id)

    resp = api_client.post(
        f"/api/reviews/{topic.id}", json={"quality": 5}, headers=_auth(token)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["topic_id"] == topic.id
    assert body["topic_title"] == "Nucleus"
    assert body["interval_days"] == 1
    assert body["repetitions"] == 1
    assert body["is_due"] is False

    listing = api_client.get("/api/reviews", headers=_auth(token))
    assert listing.status_code == 200
    assert listing.json()["total"] == 1

    summary = api_client.get("/api/reviews/summary", headers=_auth(token)).json()
    assert summary["scheduled_count"] == 1
    assert summary["reviewed_count"] == 1
    assert summary["due_count"] == 0


def test_review_queue_surfaces_due_items(api_client, test_session):
    token = _signup(api_client).json()["access_token"]
    material_id = _material(api_client, token)
    topic, _ = _curriculum(test_session, material_id)
    user_id = _user_id(api_client, token)

    past = (datetime.now(timezone.utc) - timedelta(days=3)).replace(tzinfo=None)
    test_session.add(
        ReviewSchedule(
            user_id=user_id,
            topic_id=topic.id,
            interval_days=7,
            repetitions=3,
            due_at=past,
        )
    )
    test_session.commit()

    resp = api_client.get("/api/reviews/queue", headers=_auth(token))
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert [item["topic_id"] for item in items] == [topic.id]
    assert items[0]["is_due"] is True


def test_quiz_submission_updates_mastery_and_review(api_client, test_session):
    token = _signup(api_client).json()["access_token"]
    material_id = _material(api_client, token)
    topic, concept = _curriculum(test_session, material_id)

    lesson = Lesson(
        material_id=material_id,
        concept_id=concept.id,
        topic_id=topic.id,
        title="Lesson",
        content="content",
        status="ready",
    )
    test_session.add(lesson)
    test_session.commit()
    question = Question(
        lesson_id=lesson.id,
        concept_id=concept.id,
        type="mcq",
        prompt="Which structure?",
        options=["Nucleus", "Membrane"],
        answer="Nucleus",
        explanation="The nucleus.",
        difficulty=2,
    )
    test_session.add(question)
    test_session.commit()

    resp = api_client.post(
        f"/api/quizzes/{lesson.id}/submit",
        json={"answers": [{"question_id": question.id, "response": "Nucleus"}]},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["concept_mastery"][0]["score"] > 0

    events = list(test_session.scalars(select(MasteryEvent)))
    assert len(events) == 1
    assert events[0].source == "quiz"
    assert events[0].topic_id == topic.id

    schedule = test_session.scalar(
        select(ReviewSchedule).where(ReviewSchedule.topic_id == topic.id)
    )
    assert schedule is not None

    history = api_client.get(
        f"/api/mastery/topics/{topic.id}/history", headers=_auth(token)
    )
    assert history.status_code == 200
    assert len(history.json()) == 1

    mastery = api_client.get("/api/mastery", headers=_auth(token)).json()
    assert mastery[0]["topic_id"] == topic.id
    assert mastery[0]["mastery"] > 0


def test_reviews_require_auth(api_client):
    assert api_client.get("/api/reviews").status_code == 401
    assert api_client.get("/api/reviews/queue").status_code == 401
    assert api_client.get("/api/reviews/summary").status_code == 401
    assert api_client.post("/api/reviews/1", json={"quality": 5}).status_code == 401
    assert api_client.get("/api/mastery").status_code == 401


def test_reviews_scoped_to_owner(api_client, test_session):
    owner = _signup(api_client, email="owner@example.com").json()["access_token"]
    other = _signup(api_client, email="other@example.com").json()["access_token"]
    material_id = _material(api_client, owner)
    topic, _ = _curriculum(test_session, material_id)

    assert (
        api_client.post(
            f"/api/reviews/{topic.id}", json={"quality": 5}, headers=_auth(other)
        ).status_code
        == 404
    )
    assert (
        api_client.get(
            f"/api/mastery/topics/{topic.id}/history", headers=_auth(other)
        ).status_code
        == 404
    )


def test_student_row_links_review_schedule(api_client, test_session):
    token = _signup(api_client).json()["access_token"]
    user_id = _user_id(api_client, token)
    _material(api_client, token)
    student = test_session.scalar(
        select(Student).where(Student.user_id == user_id)
    )
    assert student is not None
