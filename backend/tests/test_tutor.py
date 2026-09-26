from __future__ import annotations

from sqlalchemy import select

from app.llm import LLMError
from app.models import Chunk, TutorConversation, TutorMessage
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
    from app.models import Chapter, Subject, Topic

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


class _FakeLLM:
    def __init__(self, reply="What do you think the nucleus does?"):
        self.reply = reply
        self.calls: list[dict] = []

    def complete(self, messages, *, system=None, temperature=0.3, max_tokens=2048):
        self.calls.append({"messages": messages, "system": system})
        return self.reply

    def embed(self, texts):
        return [[0.0] for _ in texts]


class _FailingLLM:
    def complete(self, messages, *, system=None, temperature=0.3, max_tokens=2048):
        raise LLMError("provider down")

    def embed(self, texts):
        return [[0.0] for _ in texts]


def test_tutor_endpoints_require_auth(api_client):
    assert api_client.get("/api/tutor/conversations").status_code == 401
    assert (
        api_client.post("/api/tutor/conversations", json={}).status_code == 401
    )
    assert api_client.get("/api/tutor/conversations/1").status_code == 401
    assert (
        api_client.post(
            "/api/tutor/conversations/1/messages", json={"content": "hi"}
        ).status_code
        == 401
    )
    assert api_client.delete("/api/tutor/conversations/1").status_code == 401


def test_create_and_list_conversation(api_client, test_session):
    token = _signup(api_client).json()["access_token"]
    material_id = _material(api_client, token)
    topic = _topic(test_session, material_id)

    resp = api_client.post(
        "/api/tutor/conversations",
        json={"topic_id": topic.id},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["topic_id"] == topic.id
    assert body["title"] == "Nucleus"
    assert body["language"] == "en"

    listing = api_client.get(
        "/api/tutor/conversations", headers=_auth(token)
    ).json()
    assert len(listing) == 1
    assert listing[0]["topic_title"] == "Nucleus"
    assert listing[0]["message_count"] == 0


def test_send_message_persists_and_grounds(api_client, test_session, monkeypatch):
    fake = _FakeLLM()
    monkeypatch.setattr(tutor_service, "get_llm", lambda: fake)

    token = _signup(api_client).json()["access_token"]
    material_id = _material(api_client, token)
    topic = _topic(test_session, material_id)

    test_session.add(
        Chunk(material_id=material_id, index=0, content="The nucleus stores DNA.")
    )
    test_session.commit()

    conversation_id = api_client.post(
        "/api/tutor/conversations",
        json={"topic_id": topic.id},
        headers=_auth(token),
    ).json()["id"]

    resp = api_client.post(
        f"/api/tutor/conversations/{conversation_id}/messages",
        json={"content": "What does the nucleus do?"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_message"]["role"] == "user"
    assert body["reply"]["role"] == "assistant"
    assert body["reply"]["content"] == fake.reply
    assert body["reply"]["grounding"][0]["chunk_id"] > 0

    # The Socratic system prompt is grounded in the source excerpt.
    assert "The nucleus stores DNA." in fake.calls[0]["system"]

    detail = api_client.get(
        f"/api/tutor/conversations/{conversation_id}", headers=_auth(token)
    ).json()
    assert [m["role"] for m in detail["messages"]] == ["user", "assistant"]

    stored = list(
        test_session.scalars(
            select(TutorMessage).where(
                TutorMessage.conversation_id == conversation_id
            )
        )
    )
    assert len(stored) == 2


def test_conversation_is_scoped_to_owner(api_client, test_session):
    owner = _signup(api_client, email="owner@example.com").json()["access_token"]
    other = _signup(api_client, email="other@example.com").json()["access_token"]
    material_id = _material(api_client, owner)
    topic = _topic(test_session, material_id)

    conversation_id = api_client.post(
        "/api/tutor/conversations",
        json={"topic_id": topic.id},
        headers=_auth(owner),
    ).json()["id"]

    assert (
        api_client.get(
            f"/api/tutor/conversations/{conversation_id}", headers=_auth(other)
        ).status_code
        == 404
    )
    assert (
        api_client.post(
            f"/api/tutor/conversations/{conversation_id}/messages",
            json={"content": "hi"},
            headers=_auth(other),
        ).status_code
        == 404
    )
    assert (
        api_client.delete(
            f"/api/tutor/conversations/{conversation_id}", headers=_auth(other)
        ).status_code
        == 404
    )


def test_create_conversation_rejects_foreign_topic(api_client, test_session):
    owner = _signup(api_client, email="owner@example.com").json()["access_token"]
    other = _signup(api_client, email="other@example.com").json()["access_token"]
    material_id = _material(api_client, owner)
    topic = _topic(test_session, material_id)

    resp = api_client.post(
        "/api/tutor/conversations",
        json={"topic_id": topic.id},
        headers=_auth(other),
    )
    assert resp.status_code == 404


def test_delete_conversation_removes_messages(api_client, test_session, monkeypatch):
    fake = _FakeLLM()
    monkeypatch.setattr(tutor_service, "get_llm", lambda: fake)

    token = _signup(api_client).json()["access_token"]
    material_id = _material(api_client, token)
    topic = _topic(test_session, material_id)
    conversation_id = api_client.post(
        "/api/tutor/conversations",
        json={"topic_id": topic.id},
        headers=_auth(token),
    ).json()["id"]
    api_client.post(
        f"/api/tutor/conversations/{conversation_id}/messages",
        json={"content": "hello"},
        headers=_auth(token),
    )

    assert (
        api_client.delete(
            f"/api/tutor/conversations/{conversation_id}", headers=_auth(token)
        ).status_code
        == 204
    )
    assert (
        api_client.get(
            f"/api/tutor/conversations/{conversation_id}", headers=_auth(token)
        ).status_code
        == 404
    )
    assert (
        list(
            test_session.scalars(
                select(TutorMessage).where(
                    TutorMessage.conversation_id == conversation_id
                )
            )
        )
        == []
    )
    assert test_session.scalar(select(TutorConversation)) is None


def test_llm_failure_returns_502_and_keeps_user_message(
    api_client, test_session, monkeypatch
):
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
        json={"content": "explain"},
        headers=_auth(token),
    )
    assert resp.status_code == 502

    stored = list(
        test_session.scalars(
            select(TutorMessage).where(
                TutorMessage.conversation_id == conversation_id
            )
        )
    )
    assert len(stored) == 1
    assert stored[0].role == "user"
