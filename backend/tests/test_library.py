from __future__ import annotations


def _signup(client, email="student@example.com"):
    response = client.post(
        "/api/auth/signup",
        json={"email": email, "password": "password123", "display_name": "Student"},
    )
    return response.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_folder_create_move_rename_and_empty_delete(api_client):
    token = _signup(api_client)
    headers = _auth(token)
    parent = api_client.post(
        "/api/folders", json={"name": "Science"}, headers=headers
    )
    assert parent.status_code == 201
    child = api_client.post(
        "/api/folders",
        json={"name": "Biology", "parent_id": parent.json()["id"]},
        headers=headers,
    )
    assert child.status_code == 201

    material = api_client.post(
        "/api/materials/text",
        json={"title": "Cells", "text": "Cell notes"},
        headers=headers,
    )
    material_id = material.json()["id"]
    moved = api_client.patch(
        f"/api/materials/{material_id}/folder",
        json={"folder_id": child.json()["id"]},
        headers=headers,
    )
    assert moved.status_code == 200
    assert moved.json()["folder_id"] == child.json()["id"]

    conflict = api_client.delete(
        f"/api/folders/{parent.json()['id']}", headers=headers
    )
    assert conflict.status_code == 409

    renamed = api_client.patch(
        f"/api/folders/{child.json()['id']}",
        json={"name": "Cell biology"},
        headers=headers,
    )
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Cell biology"

    api_client.patch(
        f"/api/materials/{material_id}/folder",
        json={"folder_id": None},
        headers=headers,
    )
    assert api_client.delete(
        f"/api/folders/{child.json()['id']}", headers=headers
    ).status_code == 204


def test_folders_are_private_and_cycles_are_rejected(api_client):
    owner_token = _signup(api_client, "owner@example.com")
    other_token = _signup(api_client, "other@example.com")
    folder = api_client.post(
        "/api/folders", json={"name": "Private"}, headers=_auth(owner_token)
    )
    folder_id = folder.json()["id"]

    assert api_client.get("/api/folders", headers=_auth(other_token)).json() == []
    assert api_client.patch(
        f"/api/folders/{folder_id}",
        json={"name": "Stolen"},
        headers=_auth(other_token),
    ).status_code == 404

    child = api_client.post(
        "/api/folders",
        json={"name": "Child", "parent_id": folder_id},
        headers=_auth(owner_token),
    )
    cycle = api_client.patch(
        f"/api/folders/{folder_id}",
        json={"parent_id": child.json()["id"]},
        headers=_auth(owner_token),
    )
    assert cycle.status_code == 409


def test_text_upload_limit_is_enforced(api_client):
    token = _signup(api_client)
    response = api_client.post(
        "/api/materials/text",
        json={"title": "Too long", "text": "a" * 100_001},
        headers=_auth(token),
    )
    assert response.status_code == 422
    assert "100000" in response.text


def test_file_upload_size_limit_is_enforced(api_client):
    token = _signup(api_client)
    response = api_client.post(
        "/api/materials",
        files={"file": ("large.txt", b"x" * (50 * 1024 * 1024 + 1), "text/plain")},
        headers=_auth(token),
    )
    assert response.status_code == 413
    assert "50 MB" in response.json()["detail"]
