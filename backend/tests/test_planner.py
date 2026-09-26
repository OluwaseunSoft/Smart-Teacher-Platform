from __future__ import annotations

from datetime import date, timedelta

from app.models import Chapter, Subject, Topic

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


def _topics(session, material_id, count=3, difficulty="core"):
    subject = Subject(material_id=material_id, name="Biology", order_index=0)
    session.add(subject)
    session.commit()
    chapter = Chapter(subject_id=subject.id, title="Cells", order_index=0)
    session.add(chapter)
    session.commit()
    topics = []
    for i in range(count):
        topic = Topic(
            chapter_id=chapter.id,
            title=f"Topic {i}",
            difficulty=difficulty,
            order_index=i,
        )
        session.add(topic)
        session.commit()
        topics.append(topic)
    return topics


def _future(days=10) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


def test_planner_requires_auth(api_client):
    assert api_client.get("/api/planner/exams").status_code == 401
    assert api_client.post("/api/planner/exams", json={}).status_code == 401
    assert api_client.get("/api/planner/plans").status_code == 401
    assert api_client.post("/api/planner/plans", json={}).status_code == 401


def test_create_exam_and_generate_plan(api_client, test_session):
    token = _signup(api_client).json()["access_token"]
    material_id = _material(api_client, token)
    _topics(test_session, material_id, count=3)

    exam = api_client.post(
        "/api/planner/exams",
        json={"title": "Midterm", "exam_date": _future(10)},
        headers=_auth(token),
    )
    assert exam.status_code == 201
    exam_id = exam.json()["id"]

    plan = api_client.post(
        "/api/planner/plans",
        json={"exam_date_id": exam_id, "daily_minutes": 60},
        headers=_auth(token),
    )
    assert plan.status_code == 201
    assert plan.json()["status"] == "active"
    plan_id = plan.json()["id"]

    detail = api_client.get(
        f"/api/planner/plans/{plan_id}", headers=_auth(token)
    ).json()
    assert detail["total_items"] == 3
    assert detail["completed_items"] == 0
    assert detail["percent_complete"] == 0.0
    assert detail["exam_title"] == "Midterm"
    assert detail["items"][0]["topic_title"].startswith("Topic")

    item_id = detail["items"][0]["id"]
    updated = api_client.patch(
        f"/api/planner/plans/{plan_id}/items/{item_id}",
        json={"status": "done"},
        headers=_auth(token),
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "done"
    assert updated.json()["completed_at"] is not None

    detail = api_client.get(
        f"/api/planner/plans/{plan_id}", headers=_auth(token)
    ).json()
    assert detail["completed_items"] == 1
    assert detail["percent_complete"] > 0


def test_plan_distributes_topics_across_days(api_client, test_session):
    token = _signup(api_client).json()["access_token"]
    material_id = _material(api_client, token)
    _topics(test_session, material_id, count=4, difficulty="core")

    exam_id = api_client.post(
        "/api/planner/exams",
        json={"title": "Final", "exam_date": _future(20)},
        headers=_auth(token),
    ).json()["id"]
    plan_id = api_client.post(
        "/api/planner/plans",
        json={"exam_date_id": exam_id, "daily_minutes": 30},
        headers=_auth(token),
    ).json()["id"]

    detail = api_client.get(
        f"/api/planner/plans/{plan_id}", headers=_auth(token)
    ).json()
    days = {item["scheduled_for"] for item in detail["items"]}
    assert len(days) == 4


def test_generating_plan_archives_previous(api_client, test_session):
    token = _signup(api_client).json()["access_token"]
    material_id = _material(api_client, token)
    _topics(test_session, material_id, count=2)

    exam_id = api_client.post(
        "/api/planner/exams",
        json={"title": "Quiz", "exam_date": _future(10)},
        headers=_auth(token),
    ).json()["id"]

    first = api_client.post(
        "/api/planner/plans",
        json={"exam_date_id": exam_id},
        headers=_auth(token),
    ).json()["id"]
    second = api_client.post(
        "/api/planner/plans",
        json={"exam_date_id": exam_id},
        headers=_auth(token),
    ).json()["id"]

    plans = {
        plan["id"]: plan["status"]
        for plan in api_client.get(
            "/api/planner/plans", headers=_auth(token)
        ).json()
    }
    assert plans[first] == "archived"
    assert plans[second] == "active"


def test_planner_scoped_to_owner(api_client, test_session):
    owner = _signup(api_client, email="owner@example.com").json()["access_token"]
    other = _signup(api_client, email="other@example.com").json()["access_token"]
    material_id = _material(api_client, owner)
    _topics(test_session, material_id, count=2)

    exam_id = api_client.post(
        "/api/planner/exams",
        json={"title": "Midterm", "exam_date": _future(10)},
        headers=_auth(owner),
    ).json()["id"]
    plan_id = api_client.post(
        "/api/planner/plans",
        json={"exam_date_id": exam_id},
        headers=_auth(owner),
    ).json()["id"]

    assert (
        api_client.get(f"/api/planner/plans/{plan_id}", headers=_auth(other)).status_code
        == 404
    )
    assert (
        api_client.get(f"/api/planner/exams", headers=_auth(other)).json() == []
    )
    assert (
        api_client.delete(
            f"/api/planner/exams/{exam_id}", headers=_auth(other)
        ).status_code
        == 404
    )


def test_deleting_exam_removes_plan(api_client, test_session):
    token = _signup(api_client).json()["access_token"]
    material_id = _material(api_client, token)
    _topics(test_session, material_id, count=2)

    exam_id = api_client.post(
        "/api/planner/exams",
        json={"title": "Midterm", "exam_date": _future(10)},
        headers=_auth(token),
    ).json()["id"]
    api_client.post(
        "/api/planner/plans",
        json={"exam_date_id": exam_id},
        headers=_auth(token),
    )

    assert (
        api_client.delete(
            f"/api/planner/exams/{exam_id}", headers=_auth(token)
        ).status_code
        == 204
    )
    assert api_client.get("/api/planner/plans", headers=_auth(token)).json() == []
