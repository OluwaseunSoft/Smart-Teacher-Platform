from __future__ import annotations

from sqlalchemy import select

from app.models import Chapter, Chunk, Material, Student, Subject, Topic, TopicChunk
from app.services import structuring

PASSWORD = "password123"


def _signup(client, email="student@example.com", name="Student"):
    return client.post(
        "/api/auth/signup",
        json={"email": email, "password": PASSWORD, "display_name": name},
    )


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_material(client, token, title="Biology"):
    resp = client.post(
        "/api/materials/text",
        json={"title": title, "text": "Cells are the basic unit of life."},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    return resp.json()["id"]


class _FakeLLM:
    def generate_json(self, messages, system=None):  # noqa: ANN001
        return {
            "title": "Biology",
            "concepts": [
                {
                    "title": "Cell Structure",
                    "summary": "Parts of a cell",
                    "difficulty": "intro",
                    "subconcepts": [
                        {"title": "Nucleus", "summary": "Control center"},
                        {"title": "Mitochondria", "summary": "Powerhouse"},
                    ],
                },
                {
                    "title": "Cell Division",
                    "summary": "How cells reproduce",
                    "difficulty": "core",
                },
            ],
        }


def test_build_curriculum_creates_hierarchy_and_grounding(db_session, monkeypatch):
    monkeypatch.setattr(structuring, "get_llm", lambda: _FakeLLM())

    student = Student(name="T")
    material = Material(student_id=1, title="M", raw_text="cell biology content")
    db_session.add_all([student, material])
    db_session.commit()

    db_session.add_all(
        [
            Chunk(material_id=material.id, index=0, content="nucleus control center"),
            Chunk(material_id=material.id, index=1, content="mitochondria powerhouse"),
        ]
    )
    db_session.commit()

    concepts = structuring.build_curriculum(db_session, material)
    assert len(concepts) == 3

    subject = db_session.scalar(
        select(Subject).where(Subject.material_id == material.id)
    )
    assert subject is not None
    assert subject.name == "Biology"

    chapters = list(
        db_session.scalars(
            select(Chapter).where(Chapter.subject_id == subject.id).order_by(Chapter.order_index)
        )
    )
    assert [c.title for c in chapters] == ["Cell Structure", "Cell Division"]

    topics = list(
        db_session.scalars(
            select(Topic).join(Chapter).where(Chapter.subject_id == subject.id)
        )
    )
    assert len(topics) == 3
    assert all(topic.concept_id is not None for topic in topics)

    links = db_session.scalars(
        select(TopicChunk).join(Topic).join(Chapter).where(Chapter.subject_id == subject.id)
    ).all()
    assert len(links) > 0


def test_curriculum_api_lists_hierarchy(api_client, test_session):
    token = _signup(api_client).json()["access_token"]
    material_id = _create_material(api_client, token)

    subject = Subject(material_id=material_id, name="Biology", order_index=0)
    test_session.add(subject)
    test_session.commit()
    chapter = Chapter(subject_id=subject.id, title="Cells", order_index=0)
    test_session.add(chapter)
    test_session.commit()
    test_session.add(Topic(chapter_id=chapter.id, title="Nucleus", order_index=0))
    test_session.commit()

    resp = api_client.get(
        f"/api/curriculum/materials/{material_id}", headers=_auth(token)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["material_id"] == material_id
    assert body["subjects"][0]["name"] == "Biology"
    assert body["subjects"][0]["chapters"][0]["topics"][0]["title"] == "Nucleus"

    listing = api_client.get("/api/curriculum", headers=_auth(token))
    assert listing.status_code == 200
    assert listing.json()[0]["material_id"] == material_id


def test_topic_detail_includes_grounding(api_client, test_session):
    token = _signup(api_client).json()["access_token"]
    material_id = _create_material(api_client, token)

    chunk = Chunk(material_id=material_id, index=2, content="nucleus content")
    test_session.add(chunk)
    test_session.commit()

    subject = Subject(material_id=material_id, name="Biology")
    test_session.add(subject)
    test_session.commit()
    chapter = Chapter(subject_id=subject.id, title="Cells")
    test_session.add(chapter)
    test_session.commit()
    topic = Topic(chapter_id=chapter.id, title="Nucleus")
    test_session.add(topic)
    test_session.commit()
    test_session.add(TopicChunk(topic_id=topic.id, chunk_id=chunk.id, relevance=0.9))
    test_session.commit()

    resp = api_client.get(f"/api/topics/{topic.id}", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Nucleus"
    assert body["source_material_id"] == material_id
    assert body["source_title"] == "Biology"
    assert body["grounding"] == [
        {
            "chunk_id": chunk.id,
            "index": 2,
            "relevance": 0.9,
            "content": "nucleus content",
        }
    ]


def test_curriculum_requires_auth(api_client):
    assert api_client.get("/api/curriculum").status_code == 401
    assert api_client.get("/api/curriculum/materials/1").status_code == 401
    assert api_client.get("/api/topics/1").status_code == 401


def test_curriculum_scoped_to_owner(api_client, test_session):
    owner = _signup(api_client, email="owner@example.com").json()["access_token"]
    other = _signup(api_client, email="other@example.com").json()["access_token"]
    material_id = _create_material(api_client, owner)

    subject = Subject(material_id=material_id, name="Biology")
    test_session.add(subject)
    test_session.commit()
    chapter = Chapter(subject_id=subject.id, title="Cells")
    test_session.add(chapter)
    test_session.commit()
    topic = Topic(chapter_id=chapter.id, title="Nucleus")
    test_session.add(topic)
    test_session.commit()

    assert (
        api_client.get(f"/api/topics/{topic.id}", headers=_auth(other)).status_code
        == 404
    )
    assert (
        api_client.get(
            f"/api/curriculum/materials/{material_id}", headers=_auth(other)
        ).status_code
        == 404
    )


def test_material_access_requires_ownership(api_client):
    owner = _signup(api_client, email="owner@example.com").json()["access_token"]
    other = _signup(api_client, email="other@example.com").json()["access_token"]
    material_id = _create_material(api_client, owner)

    assert api_client.get(f"/api/materials/{material_id}", headers=_auth(owner)).status_code == 200
    assert api_client.get(f"/api/materials/{material_id}", headers=_auth(other)).status_code == 404
    assert api_client.get("/api/materials", headers=_auth(other)).json() == []
