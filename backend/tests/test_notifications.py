from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from app.models import Chapter, ReviewSchedule, Subject, Topic
from app.services import notifications

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


def _due_review(session, user_id, topic_id):
    past = (datetime.now(timezone.utc) - timedelta(days=2)).replace(tzinfo=None)
    session.add(
        ReviewSchedule(
            user_id=user_id,
            topic_id=topic_id,
            interval_days=1,
            due_at=past,
        )
    )
    session.commit()


def test_notifications_require_auth(api_client):
    assert api_client.get("/api/notifications").status_code == 401
    assert api_client.post("/api/notifications/read-all").status_code == 401
    assert api_client.post("/api/notifications/1/read").status_code == 401


def test_due_review_generates_reminder_once(api_client, test_session):
    token = _signup(api_client).json()["access_token"]
    material_id = _material(api_client, token)
    topic = _topic(test_session, material_id)
    _due_review(test_session, _user_id(api_client, token), topic.id)

    first = api_client.get("/api/notifications", headers=_auth(token)).json()
    assert first["unread"] == 1
    assert first["items"][0]["type"] == "review_due"

    second = api_client.get("/api/notifications", headers=_auth(token)).json()
    assert second["unread"] == 1
    assert len(second["items"]) == 1


def test_plan_task_generates_reminder(api_client, test_session):
    token = _signup(api_client).json()["access_token"]
    material_id = _material(api_client, token)
    _topic(test_session, material_id)

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

    page = api_client.get("/api/notifications", headers=_auth(token)).json()
    types = {item["type"] for item in page["items"]}
    assert "plan_task" in types


def test_mark_read_and_read_all(api_client, test_session):
    token = _signup(api_client).json()["access_token"]
    material_id = _material(api_client, token)
    topic = _topic(test_session, material_id)
    _due_review(test_session, _user_id(api_client, token), topic.id)

    page = api_client.get("/api/notifications", headers=_auth(token)).json()
    notification_id = page["items"][0]["id"]

    read = api_client.post(
        f"/api/notifications/{notification_id}/read", headers=_auth(token)
    )
    assert read.status_code == 200
    assert read.json()["read_at"] is not None

    after = api_client.get("/api/notifications", headers=_auth(token)).json()
    assert after["unread"] == 0

    # A second unread notification is cleared by read-all.
    notifications.create(test_session, _user_id(api_client, token), type="info", title="Hi")
    resp = api_client.post(
        "/api/notifications/read-all", headers=_auth(token)
    )
    assert resp.status_code == 200
    assert resp.json()["updated"] == 1


def test_notifications_scoped_to_owner(api_client, test_session):
    owner = _signup(api_client, email="owner@example.com").json()["access_token"]
    other = _signup(api_client, email="other@example.com").json()["access_token"]
    owner_id = _user_id(api_client, owner)

    owner_notification = notifications.create(
        test_session, owner_id, type="info", title="Private"
    )

    assert (
        api_client.post(
            f"/api/notifications/{owner_notification.id}/read", headers=_auth(other)
        ).status_code
        == 404
    )
    page = api_client.get("/api/notifications", headers=_auth(other)).json()
    assert page["items"] == []
