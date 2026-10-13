"""Basic regression tests for the resident rotation Flask app.

Every test uses a temporary SQLite database; no local or real resident data is touched.
"""

import re

import pytest

import app as rotation_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "rotation-test.db"
    monkeypatch.setattr(rotation_app, "DB", str(test_db))
    monkeypatch.delenv("ROTATION_INITIAL_PASSWORD", raising=False)
    monkeypatch.setattr(rotation_app.app, "_ready", False, raising=False)
    rotation_app.app.config.update(TESTING=True, SECRET_KEY="test-only-secret")
    rotation_app.init()
    rotation_app.app._ready = True
    with rotation_app.app.test_client() as test_client:
        yield test_client


def csrf_token(response):
    match = re.search(rb'name="_csrf_token" value="([^"]+)"', response.data)
    assert match, "CSRF token is missing from the form"
    return match.group(1).decode()


def test_login_page_renders_password_field_without_disclosing_default(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert b'name="password"' in response.data
    assert b"Benhocine-ChangeMe-2026" not in response.data
    assert b'name="_csrf_token"' in response.data


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "/residents",
        "/terrains",
        "/capacities",
        "/assign",
        "/history",
        "/summary",
        "/decisions",
        "/settings",
        "/export",
        "/backup",
    ],
)
def test_private_pages_redirect_anonymous_users_to_login(client, path):
    response = client.get(path)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_first_admin_password_must_be_long_enough_and_confirmed(client):
    page = client.get("/login")
    token = csrf_token(page)
    response = client.post(
        "/login",
        data={
            "_csrf_token": token,
            "password": "short",
            "password_confirm": "short",
        },
    )

    assert response.status_code == 200
    assert "12".encode() in response.data


def test_first_admin_password_is_hashed_and_authenticates(client):
    page = client.get("/login")
    token = csrf_token(page)
    response = client.post(
        "/login",
        data={
            "_csrf_token": token,
            "password": "A-secure-test-password-2026",
            "password_confirm": "A-secure-test-password-2026",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
    with rotation_app.db() as connection:
        stored = connection.execute(
            "SELECT value FROM settings WHERE key='password'"
        ).fetchone()["value"]
    assert stored.startswith(("scrypt:", "pbkdf2:"))
    assert client.get("/").status_code == 200


def test_post_without_csrf_token_is_rejected(client):
    response = client.post("/login", data={"password": "anything"})

    assert response.status_code == 400
    assert b"CSRF token" in response.data


def test_invalid_password_does_not_authenticate(client):
    setup_page = client.get("/login")
    setup_token = csrf_token(setup_page)
    client.post(
        "/login",
        data={
            "_csrf_token": setup_token,
            "password": "A-secure-test-password-2026",
            "password_confirm": "A-secure-test-password-2026",
        },
    )
    client.get("/logout")

    login_page = client.get("/login")
    token = csrf_token(login_page)
    response = client.post(
        "/login",
        data={"_csrf_token": token, "password": "A-secure-but-wrong-password"},
    )

    assert response.status_code == 200
    assert b'name="password"' in response.data
    assert "Incorrect password".encode() in response.data
