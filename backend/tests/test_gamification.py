from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.models import Chapter, Concept, Lesson, Question, Student, Subject, Topic
from app.services import gamification

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


def _lesson_question(session, material_id):
    subject = Subject(material_id=material_id, name="Biology", order_index=0)
    session.add(subject)
    session.commit()
    chapter = Chapter(subject_id=subject.id, title="Cells", order_index=0)
    session.add(chapter)
    session.commit()
    concept = Concept(material_id=material_id, title="Nucleus", order_index=0)
    session.add(concept)
    session.commit()
    topic = Topic(
        chapter_id=chapter.id, concept_id=concept.id, title="Nucleus", order_index=0
    )
    session.add(topic)
    session.commit()
    lesson = Lesson(
        material_id=material_id,
        concept_id=concept.id,
        topic_id=topic.id,
        title="Lesson",
        content="content",
        status="ready",
    )
    session.add(lesson)
    session.commit()
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
    session.add(question)
    session.commit()
    return lesson, question


def test_gamification_requires_auth(api_client):
    assert api_client.get("/api/gamification/streak").status_code == 401
    assert api_client.get("/api/gamification/achievements").status_code == 401
    assert api_client.get("/api/gamification/dashboard").status_code == 401


def test_achievements_catalog_is_seeded(api_client):
    token = _signup(api_client).json()["access_token"]
    resp = api_client.get("/api/gamification/achievements", headers=_auth(token))
    assert resp.status_code == 200
    catalog = resp.json()
    assert len(catalog) == len(gamification.DEFAULT_ACHIEVEMENTS)
    assert all(item["unlocked"] is False for item in catalog)
    assert {item["code"] for item in catalog} >= {"first_steps", "quiz_ace"}


def test_quiz_unlocks_achievements_and_streak(api_client, test_session):
    token = _signup(api_client).json()["access_token"]
    material_id = _material(api_client, token)
    lesson, question = _lesson_question(test_session, material_id)

    resp = api_client.post(
        f"/api/quizzes/{lesson.id}/submit",
        json={"answers": [{"question_id": question.id, "response": "Nucleus"}]},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["score"] == 1.0

    catalog = {
        item["code"]: item
        for item in api_client.get(
            "/api/gamification/achievements", headers=_auth(token)
        ).json()
    }
    assert catalog["first_steps"]["unlocked"] is True
    assert catalog["quiz_ace"]["unlocked"] is True
    assert catalog["first_steps"]["unlocked_at"] is not None

    streak = api_client.get(
        "/api/gamification/streak", headers=_auth(token)
    ).json()
    assert streak["current"] == 1
    assert streak["today_count"] == 1


def test_streak_resets_after_a_gap(api_client, test_session):
    token = _signup(api_client).json()["access_token"]
    user_id = _user_id(api_client, token)

    gamification.record_activity(test_session, user_id, when=date(2026, 1, 1))
    gamification.record_activity(test_session, user_id, when=date(2026, 1, 2))
    streak, profile = gamification.record_activity(
        test_session, user_id, when=date(2026, 1, 3)
    )
    assert profile.streak_current == 3
    assert profile.streak_longest == 3

    _, profile = gamification.record_activity(
        test_session, user_id, when=date(2026, 1, 10)
    )
    assert profile.streak_current == 1
    assert profile.streak_longest == 3


def test_dashboard_aggregates_progress(api_client, test_session):
    token = _signup(api_client).json()["access_token"]
    material_id = _material(api_client, token)
    lesson, question = _lesson_question(test_session, material_id)

    api_client.post(
        f"/api/quizzes/{lesson.id}/submit",
        json={"answers": [{"question_id": question.id, "response": "Nucleus"}]},
        headers=_auth(token),
    )

    dashboard = api_client.get(
        "/api/gamification/dashboard", headers=_auth(token)
    ).json()
    assert dashboard["topics_total"] == 1
    assert dashboard["topics_covered"] == 1
    assert dashboard["average_mastery"] > 0
    assert dashboard["achievements_total"] == len(gamification.DEFAULT_ACHIEVEMENTS)
    assert dashboard["achievements_unlocked"] >= 1
    assert dashboard["streak"]["current"] == 1


def test_dashboard_reports_active_plan(api_client, test_session):
    from datetime import timedelta

    token = _signup(api_client).json()["access_token"]
    material_id = _material(api_client, token)
    _lesson_question(test_session, material_id)

    exam_id = api_client.post(
        "/api/planner/exams",
        json={
            "title": "Midterm",
            "exam_date": (date.today() + timedelta(days=10)).isoformat(),
        },
        headers=_auth(token),
    ).json()["id"]
    api_client.post(
        "/api/planner/plans",
        json={"exam_date_id": exam_id},
        headers=_auth(token),
    )

    dashboard = api_client.get(
        "/api/gamification/dashboard", headers=_auth(token)
    ).json()
    assert dashboard["active_plan"] is not None
    assert dashboard["active_plan"]["total_items"] == 1
    assert dashboard["active_plan"]["completed_items"] == 0


def test_student_row_exists_for_gamification(api_client, test_session):
    token = _signup(api_client).json()["access_token"]
    user_id = _user_id(api_client, token)
    _material(api_client, token)
    student = test_session.scalar(select(Student).where(Student.user_id == user_id))
    assert student is not None
