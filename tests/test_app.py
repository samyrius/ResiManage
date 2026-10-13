"""Basic regression tests for the resident rotation Flask app.

Every test uses a temporary SQLite database; no local or real resident data is touched.
"""

import pytest

import app as rotation_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "rotation-test.db"
    monkeypatch.setattr(rotation_app, "DB", str(test_db))
    monkeypatch.setattr(rotation_app.app, "_ready", False, raising=False)
    rotation_app.app.config.update(TESTING=True, SECRET_KEY="test-only-secret")
    rotation_app.init()
    rotation_app.app._ready = True
    with rotation_app.app.test_client() as test_client:
        yield test_client


def test_login_page_renders_password_field(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert b'name="password"' in response.data


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


def test_invalid_password_does_not_authenticate(client):
    response = client.post("/login", data={"password": "definitely-not-the-password"})

    assert response.status_code == 200
    assert b"name=\"password\"" in response.data
    assert b"Incorrect password" in response.data or "كلمة المرور غير صحيحة".encode() in response.data


def test_language_switch_redirects_to_login_when_no_referrer(client):
    response = client.get("/lang/en")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
