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
        "/audit",
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
    assert "كلمة المرور غير صحيحة".encode() in response.data


def test_legacy_sha256_password_is_upgraded_after_successful_login(client):
    import hashlib

    legacy_password = "Legacy-password-for-migration"
    with rotation_app.db() as connection:
        connection.execute(
            "INSERT INTO settings(key,value) VALUES('password',?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (hashlib.sha256(legacy_password.encode()).hexdigest(),),
        )
        connection.commit()

    page = client.get("/login")
    token = csrf_token(page)
    response = client.post(
        "/login",
        data={"_csrf_token": token, "password": legacy_password},
    )

    assert response.status_code == 302
    with rotation_app.db() as connection:
        stored = connection.execute(
            "SELECT value FROM settings WHERE key='password'"
        ).fetchone()["value"]
    assert stored.startswith(("scrypt:", "pbkdf2:"))


def test_seed_contains_all_19_terrains_and_correct_optional_categories(client):
    with rotation_app.db() as connection:
        rows = connection.execute("SELECT name,kind FROM terrains").fetchall()

    by_name = {row["name"]: row["kind"] for row in rows}
    optional = {name for name, kind in by_name.items() if kind == "optional"}

    assert len(by_name) == 19
    assert optional == {
        "Sédation",
        "Maxillo-faciale",
        "Chirurgie cardiaque",
        "Brûlés",
        "CAC DBK",
    }
    assert by_name["Gynécologie"] != "optional"


def test_assignment_requires_capacity_and_rejects_duplicate_period(client):
    with rotation_app.db() as connection:
        year_label = rotation_app.setting(connection, "year")
        resident_id = connection.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES('Test','Resident',2)"
        ).lastrowid
        terrain_id = connection.execute(
            "SELECT id FROM terrains WHERE kind!='optional' ORDER BY id LIMIT 1"
        ).fetchone()["id"]
        periods = connection.execute(
            "SELECT id FROM periods WHERE year_label=? ORDER BY id", (year_label,)
        ).fetchall()
        period_id = periods[0]["id"]
        connection.commit()

        with rotation_app.app.test_request_context("/"):
            ok, message, status = rotation_app.check(
                connection, resident_id, terrain_id, period_id, year_label
            )
        assert not ok
        assert "حدّد السعة" in message
        assert status is None

        connection.execute(
            "INSERT INTO capacities(year_label,terrain_id,period_id,places) VALUES(?,?,?,1)",
            (year_label, terrain_id, period_id),
        )
        connection.commit()
        with rotation_app.app.test_request_context("/"):
            ok, _, status = rotation_app.check(
                connection, resident_id, terrain_id, period_id, year_label
            )
        assert ok and status == "confirmed"

        connection.execute(
            "INSERT INTO assignments(resident_id,terrain_id,period_id,status) VALUES(?,?,?,'confirmed')",
            (resident_id, terrain_id, period_id),
        )
        connection.commit()
        with rotation_app.app.test_request_context("/"):
            ok, message, _ = rotation_app.check(
                connection, resident_id, terrain_id, period_id, year_label
            )
        assert not ok
        assert "مصلحة" in message


def test_repeating_core_terrain_is_blocked_until_all_core_terrains_are_done(client):
    with rotation_app.db() as connection:
        year_label = rotation_app.setting(connection, "year")
        resident_id = connection.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES('Test','Repeater',3)"
        ).lastrowid
        core_terrains = connection.execute(
            "SELECT id FROM terrains WHERE kind IN ('mandatory','basic') ORDER BY id"
        ).fetchall()
        terrain_id = core_terrains[0]["id"]
        periods = connection.execute(
            "SELECT id FROM periods WHERE year_label=? ORDER BY id", (year_label,)
        ).fetchall()
        first_period, second_period = periods[0]["id"], periods[1]["id"]
        connection.execute(
            "INSERT INTO assignments(resident_id,terrain_id,period_id,status) VALUES(?,?,?,'confirmed')",
            (resident_id, terrain_id, first_period),
        )
        connection.execute(
            "INSERT INTO capacities(year_label,terrain_id,period_id,places) VALUES(?,?,?,1)",
            (year_label, terrain_id, second_period),
        )
        connection.commit()

        with rotation_app.app.test_request_context("/"):
            ok, message, _ = rotation_app.check(
                connection, resident_id, terrain_id, second_period, year_label
            )
        assert not ok
        assert "سبق للمقيم" in message

        for row in core_terrains[1:]:
            connection.execute(
                "INSERT INTO history(resident_id,terrain_id,year_label,period,date_done) VALUES(?,?,?,?,?)",
                (resident_id, row["id"], year_label, "historique", "2026-01-01"),
            )
        connection.commit()
        with rotation_app.app.test_request_context("/"):
            ok, _, status = rotation_app.check(
                connection, resident_id, terrain_id, second_period, year_label
            )
        assert ok and status == "confirmed"


def test_resident_changes_are_written_to_audit_log(client):
    with client.session_transaction() as browser_session:
        browser_session["user"] = "admin"
        browser_session["lang"] = "en"

    form_page = client.get("/residents")
    token = csrf_token(form_page)
    response = client.post(
        "/residents",
        data={
            "_csrf_token": token,
            "surname": "AuditTest",
            "firstname": "Resident",
            "year": "2",
            "phone": "",
        },
    )
    assert response.status_code == 200

    audit_page = client.get("/audit")
    assert audit_page.status_code == 200
    assert b"resident_add" in audit_page.data
    assert b"AuditTest Resident" in audit_page.data
