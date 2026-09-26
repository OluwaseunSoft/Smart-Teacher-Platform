from __future__ import annotations

from sqlalchemy import select

from app.models import ROLE_ADMIN, User

PASSWORD = "password123"


def _signup(client, email="student@example.com", name="Student"):
    return client.post(
        "/api/auth/signup",
        json={"email": email, "password": PASSWORD, "display_name": name},
    )


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _promote_to_admin(session, email: str) -> None:
    user = session.scalar(select(User).where(User.email == email))
    user.role = ROLE_ADMIN
    session.add(user)
    session.commit()


def test_signup_login_and_me(api_client):
    resp = _signup(api_client)
    assert resp.status_code == 201
    body = resp.json()
    assert body["access_token"] and body["refresh_token"]

    me = api_client.get("/api/auth/me", headers=_auth(body["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == "student@example.com"
    assert me.json()["role"] == "student"

    login = api_client.post(
        "/api/auth/login",
        json={"email": "student@example.com", "password": PASSWORD},
    )
    assert login.status_code == 200


def test_signup_normalizes_email(api_client):
    resp = _signup(api_client, email="  MixedCase@Example.COM ")
    assert resp.status_code == 201
    assert resp.json()["access_token"]


def test_duplicate_signup_conflicts(api_client):
    assert _signup(api_client).status_code == 201
    assert _signup(api_client).status_code == 409


def test_weak_password_rejected(api_client):
    resp = api_client.post(
        "/api/auth/signup",
        json={"email": "a@b.com", "password": "short", "display_name": "A"},
    )
    assert resp.status_code == 422


def test_wrong_password_rejected(api_client):
    _signup(api_client)
    resp = api_client.post(
        "/api/auth/login",
        json={"email": "student@example.com", "password": "wrong-password"},
    )
    assert resp.status_code == 401


def test_protected_endpoint_requires_token(api_client):
    assert api_client.get("/api/auth/me").status_code == 401
    assert api_client.get("/api/auth/me", headers=_auth("garbage")).status_code == 401


def test_logout_revokes_token(api_client):
    token = _signup(api_client).json()["access_token"]
    assert api_client.post("/api/auth/logout", headers=_auth(token)).status_code == 204
    assert api_client.get("/api/auth/me", headers=_auth(token)).status_code == 401


def test_refresh_rotates_and_rejects_reuse(api_client):
    tokens = _signup(api_client).json()
    first = api_client.post(
        "/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert first.status_code == 200
    assert first.json()["access_token"]

    reused = api_client.post(
        "/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert reused.status_code == 401


def test_password_reset_flow(api_client):
    _signup(api_client)
    req = api_client.post(
        "/api/auth/password-reset/request", json={"email": "student@example.com"}
    )
    assert req.status_code == 200
    reset_token = req.json()["reset_token"]
    assert reset_token

    confirm = api_client.post(
        "/api/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": "newpassword456"},
    )
    assert confirm.status_code == 200

    assert (
        api_client.post(
            "/api/auth/login",
            json={"email": "student@example.com", "password": PASSWORD},
        ).status_code
        == 401
    )
    assert (
        api_client.post(
            "/api/auth/login",
            json={"email": "student@example.com", "password": "newpassword456"},
        ).status_code
        == 200
    )


def test_password_reset_unknown_email_is_opaque(api_client):
    resp = api_client.post(
        "/api/auth/password-reset/request", json={"email": "nobody@example.com"}
    )
    assert resp.status_code == 200
    assert resp.json()["reset_token"] is None


def test_student_cannot_access_admin(api_client):
    token = _signup(api_client).json()["access_token"]
    assert api_client.get("/api/admin/users", headers=_auth(token)).status_code == 403


def test_admin_can_list_and_search_users(api_client, test_session):
    token = _signup(api_client).json()["access_token"]
    _signup(api_client, email="second@example.com", name="Second")
    _promote_to_admin(test_session, "student@example.com")

    listing = api_client.get("/api/admin/users", headers=_auth(token))
    assert listing.status_code == 200
    assert listing.json()["total"] == 2

    search = api_client.get("/api/admin/users?q=second", headers=_auth(token))
    assert search.json()["total"] == 1
    assert search.json()["items"][0]["email"] == "second@example.com"


def test_deactivated_user_is_locked_out(api_client, test_session):
    admin_token = _signup(api_client).json()["access_token"]
    student = _signup(api_client, email="victim@example.com").json()
    _promote_to_admin(test_session, "student@example.com")

    victim = test_session.scalar(select(User).where(User.email == "victim@example.com"))
    resp = api_client.post(
        f"/api/admin/users/{victim.id}/deactivate", headers=_auth(admin_token)
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    assert api_client.get("/api/auth/me", headers=_auth(student["access_token"])).status_code == 401
    assert (
        api_client.post(
            "/api/auth/login",
            json={"email": "victim@example.com", "password": PASSWORD},
        ).status_code
        == 403
    )

    reactivate = api_client.post(
        f"/api/admin/users/{victim.id}/reactivate", headers=_auth(admin_token)
    )
    assert reactivate.status_code == 200
    assert (
        api_client.post(
            "/api/auth/login",
            json={"email": "victim@example.com", "password": PASSWORD},
        ).status_code
        == 200
    )


def test_admin_cannot_deactivate_self(api_client, test_session):
    token = _signup(api_client).json()["access_token"]
    _promote_to_admin(test_session, "student@example.com")
    me = api_client.get("/api/auth/me", headers=_auth(token)).json()
    resp = api_client.post(
        f"/api/admin/users/{me['id']}/deactivate", headers=_auth(token)
    )
    assert resp.status_code == 400


def test_audit_log_records_signup_and_login(api_client, test_session):
    token = _signup(api_client).json()["access_token"]
    _promote_to_admin(test_session, "student@example.com")
    api_client.post(
        "/api/auth/login",
        json={"email": "student@example.com", "password": PASSWORD},
    )

    logs = api_client.get("/api/admin/audit-logs", headers=_auth(token))
    assert logs.status_code == 200
    actions = {entry["action"] for entry in logs.json()}
    assert "auth.signup" in actions
    assert "auth.login" in actions
