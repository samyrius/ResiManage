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
    monkeypatch.setattr(rotation_app, "UPLOAD_DIR", str(tmp_path / "uploads" / "residents"))
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
        "/profiles",
        "/objectives",
        "/import",
        "/promotions",
        "/dems-archive",
        "/terrains",
        "/capacities",
        "/assign",
        "/history",
        "/summary",
        "/decisions",
        "/audit",
        "/users",
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

    rotation_app.init()
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
        browser_session["role"] = "super_admin"
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


def authenticated(client):
    with client.session_transaction() as browser_session:
        browser_session["user"] = "admin"
        browser_session["role"] = "super_admin"
        browser_session["lang"] = "en"


def test_profile_saves_birth_details_and_exam_scores(client):
    with rotation_app.db() as connection:
        resident_id = connection.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES('Profile','Resident',1)"
        ).lastrowid
        connection.commit()
    authenticated(client)

    page = client.get(f"/profiles/{resident_id}")
    response = client.post(
        f"/profiles/{resident_id}",
        data={
            "_csrf_token": csrf_token(page),
            "action": "profile",
            "birth_place": "Tizi Ouzou",
            "birth_date": "2000-01-02",
            "phone": "0550000000",
        },
    )
    assert response.status_code == 200

    page = client.get(f"/profiles/{resident_id}")
    response = client.post(
        f"/profiles/{resident_id}",
        data={
            "_csrf_token": csrf_token(page),
            "action": "exam",
            "study_year": "1",
            "module": "Module A",
            "theory_score": "12",
            "practical_score": "14",
        },
    )
    assert response.status_code == 200
    profile = client.get(f"/profiles/{resident_id}")
    assert b"Tizi Ouzou" in profile.data
    assert b"Module A" in profile.data
    with rotation_app.db() as connection:
        resident = connection.execute(
            "SELECT birth_place,birth_date,phone FROM residents WHERE id=?",
            (resident_id,),
        ).fetchone()
        assert tuple(resident) == ("Tizi Ouzou", "2000-01-02", "0550000000")


def test_first_year_promotion_requires_all_configured_modules(client):
    with rotation_app.db() as connection:
        resident_id = connection.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES('Promotion','Candidate',1)"
        ).lastrowid
        connection.execute(
            "INSERT INTO settings(key,value) VALUES('year1_required_modules','Module A;Module B')"
        )
        connection.execute(
            "INSERT INTO resident_exams(resident_id,study_year,module,theory_score,practical_score) VALUES(?,1,'Module A',12,12)",
            (resident_id,),
        )
        connection.commit()
    authenticated(client)

    page = client.get(f"/profiles/{resident_id}")
    response = client.post(
        f"/profiles/{resident_id}",
        data={"_csrf_token": csrf_token(page), "action": "advance"},
    )
    assert response.status_code == 200
    with rotation_app.db() as connection:
        year = connection.execute(
            "SELECT year FROM residents WHERE id=?", (resident_id,)
        ).fetchone()["year"]
    assert year == 1

    page = client.get(f"/profiles/{resident_id}")
    response = client.post(
        f"/profiles/{resident_id}",
        data={
            "_csrf_token": csrf_token(page),
            "action": "exam",
            "study_year": "1",
            "module": "Module B",
            "theory_score": "13",
            "practical_score": "11",
        },
    )
    assert response.status_code == 200
    page = client.get(f"/profiles/{resident_id}")
    response = client.post(
        f"/profiles/{resident_id}",
        data={"_csrf_token": csrf_token(page), "action": "advance"},
    )
    assert response.status_code == 200
    with rotation_app.db() as connection:
        year = connection.execute(
            "SELECT year FROM residents WHERE id=?", (resident_id,)
        ).fetchone()["year"]
    assert year == 2


def test_first_year_promotion_rejects_any_module_component_below_ten(client):
    with rotation_app.db() as connection:
        resident_id = connection.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES('Low','Score',1)"
        ).lastrowid
        connection.execute(
            "INSERT INTO settings(key,value) VALUES('year1_required_modules','Module A')"
        )
        connection.execute(
            "INSERT INTO resident_exams(resident_id,study_year,module,theory_score,practical_score) VALUES(?,1,'Module A',9.99,18)",
            (resident_id,),
        )
        connection.commit()
    authenticated(client)
    page = client.get(f"/profiles/{resident_id}")
    client.post(
        f"/profiles/{resident_id}",
        data={"_csrf_token": csrf_token(page), "action": "advance"},
    )
    with rotation_app.db() as connection:
        year = connection.execute(
            "SELECT year FROM residents WHERE id=?", (resident_id,)
        ).fetchone()["year"]
    assert year == 1


def test_admin_account_can_be_created_and_operator_is_restricted(client):
    page = client.get("/login")
    response = client.post(
        "/login",
        data={
            "_csrf_token": csrf_token(page),
            "username": "admin",
            "password": "A-secure-test-password-2026",
            "password_confirm": "A-secure-test-password-2026",
        },
    )
    assert response.status_code == 302
    page = client.get("/users")
    response = client.post(
        "/users",
        data={
            "_csrf_token": csrf_token(page),
            "username": "operator1",
            "display_name": "Rotation Operator",
            "password": "Operator-secure-password-2026",
            "role": "operator",
        },
    )
    assert response.status_code == 200
    with client.session_transaction() as browser_session:
        browser_session.clear()
    page = client.get("/login")
    response = client.post(
        "/login",
        data={
            "_csrf_token": csrf_token(page),
            "username": "operator1",
            "password": "Operator-secure-password-2026",
        },
    )
    assert response.status_code == 302
    assert client.get("/settings").status_code == 403
    assert client.get("/audit").status_code == 403
    assert client.get("/residents").status_code == 200


def test_admin_account_can_be_created_and_operator_is_restricted(client):
    page = client.get("/login")
    response = client.post(
        "/login",
        data={
            "_csrf_token": csrf_token(page),
            "username": "admin",
            "password": "A-secure-test-password-2026",
            "password_confirm": "A-secure-test-password-2026",
        },
    )
    assert response.status_code == 302
    page = client.get("/users")
    response = client.post(
        "/users",
        data={
            "_csrf_token": csrf_token(page),
            "username": "operator1",
            "display_name": "Rotation Operator",
            "password": "Operator-secure-password-2026",
            "role": "operator",
        },
    )
    assert response.status_code == 200
    with client.session_transaction() as browser_session:
        browser_session.clear()
    page = client.get("/login")
    response = client.post(
        "/login",
        data={
            "_csrf_token": csrf_token(page),
            "username": "operator1",
            "password": "Operator-secure-password-2026",
        },
    )
    assert response.status_code == 302
    assert client.get("/settings").status_code == 403
    assert client.get("/audit").status_code == 403
    assert client.get("/residents").status_code == 200


def test_year_four_dems_archive_requires_both_named_super_admins(client):
    from werkzeug.security import generate_password_hash

    with rotation_app.db() as connection:
        resident_id = connection.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES('DEMS','Candidate',4)"
        ).lastrowid
        connection.execute(
            "INSERT INTO resident_exam_records(resident_id,exam_key,virtual_score,actual_score) VALUES(?,'dems_main',12,12)",
            (resident_id,),
        )
        for username, name in (
            ("benhocine", "Professor Benhocine"),
            ("drdris", "Dr Dris"),
        ):
            connection.execute(
                "INSERT INTO admins(username,display_name,password_hash,role) VALUES(?,?,?,'super_admin')",
                (username, name, generate_password_hash("Very-strong-password-2026")),
            )
        connection.commit()

    with client.session_transaction() as browser_session:
        browser_session["user"] = "admin"
        browser_session["role"] = "super_admin"
        browser_session["lang"] = "en"

    page = client.get("/promotions")
    response = client.post(
        "/promotions",
        data={
            "_csrf_token": csrf_token(page),
            "action": "request",
            "resident": str(resident_id),
        },
    )
    assert response.status_code == 200
    with rotation_app.db() as connection:
        promotion_id = connection.execute(
            "SELECT id FROM resident_promotions WHERE resident_id=?", (resident_id,)
        ).fetchone()["id"]

    for username in ("benhocine", "drdris"):
        with client.session_transaction() as browser_session:
            browser_session["user"] = username
            browser_session["role"] = "super_admin"
        page = client.get("/promotions")
        response = client.post(
            "/promotions",
            data={
                "_csrf_token": csrf_token(page),
                "action": "vote",
                "promotion_id": str(promotion_id),
                "decision": "approve",
                "reason": "DEMS successfully passed",
            },
        )
        assert response.status_code == 200

    with rotation_app.db() as connection:
        resident = connection.execute(
            "SELECT status,year FROM residents WHERE id=?", (resident_id,)
        ).fetchone()
        archived = connection.execute(
            "SELECT approved_by FROM dems_archive WHERE resident_id=?", (resident_id,)
        ).fetchone()
        votes = connection.execute(
            "SELECT COUNT(*) FROM promotion_votes WHERE promotion_id=? AND decision='approve'",
            (promotion_id,),
        ).fetchone()[0]
    assert resident["status"] == "dems_success"
    assert resident["year"] == 4
    assert archived["approved_by"] == "benhocine,drdris"
    assert votes == 2
    assert client.get("/dems-archive").status_code == 200


def test_resident_photo_is_private_and_included_in_backup(client, tmp_path):
    import io
    import sqlite3
    import zipfile

    with rotation_app.db() as connection:
        resident_id = connection.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES('Photo','Resident',2)"
        ).lastrowid
        connection.commit()
    authenticated(client)
    page = client.get(f"/profiles/{resident_id}")
    png = b"\x89PNG\r\n\x1a\n" + b"test-image-bytes"
    response = client.post(
        f"/profiles/{resident_id}",
        data={
            "_csrf_token": csrf_token(page),
            "action": "photo",
            "photo": (io.BytesIO(png), "resident.png"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    image_response = client.get(f"/resident-photo/{resident_id}")
    assert image_response.status_code == 200
    assert image_response.data.startswith(b"\x89PNG\r\n\x1a\n")

    backup = client.get("/backup")
    assert backup.status_code == 200
    restore_dir = tmp_path / "restore"
    restore_dir.mkdir()
    with zipfile.ZipFile(io.BytesIO(backup.data)) as archive:
        names = archive.namelist()
        assert "rotation.db" in names
        assert any(name.startswith("uploads/residents/") for name in names)
        archive.extractall(restore_dir)
    restored_db = sqlite3.connect(restore_dir / "rotation.db")
    restored_count = restored_db.execute("SELECT COUNT(*) FROM residents").fetchone()[0]
    restored_db.close()
    assert restored_count == 1
    assert list((restore_dir / "uploads" / "residents").iterdir())


def test_resident_import_shows_preview_and_validates_before_saving(client):
    import io
    import re

    with client.session_transaction() as browser_session:
        browser_session["user"] = "admin"
        browser_session["role"] = "super_admin"
        browser_session["lang"] = "en"

    page = client.get("/import")
    response = client.post(
        "/import",
        data={
            "_csrf_token": csrf_token(page),
            "action": "preview",
            "file": (
                io.BytesIO(
                    "Nom,Prénom,Année,Téléphone\n"
                    "Importé,Valide,1,0550000000\n"
                    "Importé,Invalide,9,0550000001\n".encode("utf-8")
                ),
                "residents.csv",
            ),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert "Importé".encode("utf-8") in response.data
    assert b"valid rows" in response.data
    with rotation_app.db() as connection:
        assert connection.execute("SELECT COUNT(*) FROM residents").fetchone()[0] == 0

    token_match = re.search(rb'name="token" value="([^"]+)"', response.data)
    assert token_match
    response = client.post(
        "/import",
        data={
            "_csrf_token": csrf_token(response),
            "action": "confirm",
            "token": token_match.group(1).decode(),
        },
    )
    assert response.status_code == 200
    with rotation_app.db() as connection:
        rows = connection.execute(
            "SELECT surname,firstname,year,phone FROM residents"
        ).fetchall()
        history_count = connection.execute("SELECT COUNT(*) FROM history").fetchone()[0]
    assert len(rows) == 1
    assert tuple(rows[0]) == ("Importé", "Valide", 1, "0550000000")
    assert history_count == 0


def test_terrain_objectives_are_year_specific_and_profile_marks_completion(client):
    with rotation_app.db() as connection:
        resident_id = connection.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES('Objective','Resident',2)"
        ).lastrowid
        terrains = connection.execute(
            "SELECT id,name FROM terrains ORDER BY id LIMIT 2"
        ).fetchall()
        connection.execute(
            "INSERT INTO history(resident_id,terrain_id,year_label,period,date_done) VALUES(?,?,?,?,?)",
            (resident_id, terrains[0]["id"], "2025-2026", "P1", "2025-04-30"),
        )
        connection.commit()
    authenticated(client)
    page = client.get("/objectives")
    response = client.post(
        "/objectives",
        data={
            "_csrf_token": csrf_token(page),
            "terrain": str(terrains[0]["id"]),
            "study_year": "2",
            "objectives": "Airway management and safe handover",
        },
    )
    assert response.status_code == 200
    profile = client.get(f"/profiles/{resident_id}")
    assert b"Airway management and safe handover" in profile.data
    assert b'class="bad">Completed' in profile.data
    assert b'class="good">Not completed' in profile.data


def test_official_super_admin_accounts_cannot_be_demoted_or_disabled(client):
    from werkzeug.security import generate_password_hash

    with rotation_app.db() as connection:
        official_id = connection.execute(
            "INSERT INTO admins(username,display_name,password_hash,role) VALUES(?,?,?,'super_admin')",
            ("benhocine", "Professor Benhocine", generate_password_hash("Official-password-2026")),
        ).lastrowid
        connection.commit()
    authenticated(client)
    page = client.get("/users")
    response = client.post(
        "/users",
        data={
            "_csrf_token": csrf_token(page),
            "action": "toggle",
            "user_id": str(official_id),
        },
    )
    assert response.status_code == 200
    with rotation_app.db() as connection:
        account = connection.execute(
            "SELECT role,active FROM admins WHERE id=?", (official_id,)
        ).fetchone()
    assert account["role"] == "super_admin"
    assert account["active"] == 1


def test_import_adds_only_explicitly_documented_stage_history(client):
    import io
    import re

    authenticated(client)
    page = client.get("/import")
    response = client.post(
        "/import",
        data={
            "_csrf_token": csrf_token(page),
            "action": "preview",
            "file": (
                io.BytesIO(
                    "Nom,Prénom,Année,Téléphone,Terrain,Année universitaire,Période,Date de réalisation\n"
                    "Historique,Documenté,2,0550000000,Réanimation polyvalente,2024-2025,P1,2024-04-30\n"
                    "Sans,Histoire,2,0550000001,Réanimation polyvalente,,,\n".encode("utf-8")
                ),
                "residents-with-history.csv",
            ),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert b"Will import documented stage" in response.data
    assert b"Incomplete history columns" in response.data
    token_match = re.search(rb'name="token" value="([^"]+)"', response.data)
    assert token_match
    response = client.post(
        "/import",
        data={
            "_csrf_token": csrf_token(response),
            "action": "confirm",
            "token": token_match.group(1).decode(),
        },
    )
    assert response.status_code == 200
    with rotation_app.db() as connection:
        resident_count = connection.execute("SELECT COUNT(*) FROM residents").fetchone()[0]
        history = connection.execute(
            "SELECT r.surname,t.name,h.year_label,h.period,h.date_done FROM history h "
            "JOIN residents r ON r.id=h.resident_id JOIN terrains t ON t.id=h.terrain_id"
        ).fetchall()
    assert resident_count == 2
    assert len(history) == 1
    assert tuple(history[0]) == (
        "Historique",
        "Réanimation polyvalente",
        "2024-2025",
        "P1",
        "2024-04-30",
    )
