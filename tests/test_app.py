import hashlib
import os
import json
import pytest
from flask.testing import FlaskClient
import io
import sqlite3
from datetime import timedelta
import re
import zipfile
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "android" / "app" / "src" / "main" / "python"))

import app as rotation_app
import sync_client


class CsrfAwareTestClient(FlaskClient):
    def post(self, *args, **kwargs):
        path = args[0] if args else kwargs.get("path", "")
        headers = kwargs.get("headers") or {}
        if str(path).startswith("/api/sync/") and any(
            str(k).lower() == "authorization" and str(v).startswith("Bearer ")
            for k, v in headers.items()
        ):
            return super().post(*args, **kwargs)
        data = dict(kwargs.get("data") or {})
        if "_csrf_token" not in data:
            with self.session_transaction() as sess:
                token = sess.get("_csrf_token")
            if not token:
                self.get("/login")
                with self.session_transaction() as sess:
                    token = sess.get("_csrf_token")
            if token:
                data["_csrf_token"] = token
        kwargs["data"] = data
        return super().post(*args, **kwargs)


def setup_client(tmp_path, monkeypatch):
    rotation_app.app.test_client_class = CsrfAwareTestClient
    monkeypatch.setenv("ROTATION_INITIAL_PASSWORD", "test-strong-password-2026")
    monkeypatch.setattr(rotation_app, "DB", str(tmp_path / "test_rotation.db"))
    monkeypatch.setattr(rotation_app.app, "_ready", False, raising=False)
    rotation_app.app.config.update(TESTING=True, SECRET_KEY="test-only-secret")
    return rotation_app.app.test_client()


def login(client):
    return client.post("/login", data={"password": "test-strong-password-2026"}, follow_redirects=True)



def test_internal_navigation_is_grouped_responsive_and_marks_current_page(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    response = client.get("/")
    assert response.status_code == 200
    assert b'class="rt-app-shell"' in response.data
    assert 'aria-label="Navigation principale"'.encode() in response.data
    assert b'href="/leave"' in response.data
    assert b'href="/external-rotations"' in response.data
    assert "Stages et planification".encode() in response.data
    assert b'class="nav-home is-active"' in response.data
    assert b'grid-template-columns:260px minmax(0,1fr)' in response.data
    assert b'@media(max-width:680px)' in response.data
    residents = client.get("/residents")
    assert residents.status_code == 200
    assert b'href="/residents" class="is-active"' in residents.data


def test_login_page_and_language_selector(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    response = client.get("/login")
    assert response.status_code == 200
    assert b'<html lang="fr" dir="ltr">' in response.data
    assert "Français".encode() in response.data
    assert "English".encode() in response.data
    assert b'Identifiant ou e-mail' in response.data
    assert "اسم المستخدم أو البريد الإلكتروني".encode() not in response.data
    assert b'name="_csrf_token"' in response.data

def test_registration_screen_uses_selected_french_without_arabic_form_labels(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    response = client.get("/register")
    assert response.status_code == 200
    assert b'<html lang="fr" dir="ltr">' in response.data
    assert 'Nom d’utilisateur'.encode('utf-8') in response.data
    assert "اسم المستخدم".encode() not in response.data
    client.get("/lang/en", headers={"Referer": "http://localhost/register"})
    english = client.get("/register")
    assert b'<html lang="en" dir="ltr">' in english.data
    assert b'Username' in english.data
    assert "اسم المستخدم".encode() not in english.data
    client.get("/lang/ar", headers={"Referer": "http://localhost/register"})
    arabic = client.get("/register")
    assert b'<html lang="ar" dir="rtl">' in arabic.data
    assert "اسم المستخدم".encode() in arabic.data



def test_login_branding_uses_resimanage_and_navy_cyan_identity(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    response = client.get("/login")
    assert response.status_code == 200
    assert b"ResiManage" in response.data
    assert b"ResiTrack" not in response.data
    assert b"#00dff755" in response.data
    assert b"#19dfbd" in response.data
    assert b"white-space:normal;overflow-wrap:anywhere;max-width:100%;line-height:1.3;text-align:center" in response.data
    assert b"prefers-reduced-motion:reduce" in response.data
    assert b'src="/static/resimanage-3d-icon.jpg"' in response.data
    assert 'alt="ResiManage — médecin et stéthoscope"'.encode("utf-8") in response.data
    assert "💓".encode() not in response.data
    assert b'class="login-heartbeat"' in response.data
    assert b"login-heart-shape" in response.data
    assert b"login-ecg-line" in response.data
    assert b"ecg-trace" in response.data
    assert b'type="image/jpeg" href="/static/resimanage-3d-icon.jpg"' in response.data
    assert b'class="login-emblem"' in response.data
    assert "Tous droits réservés · ResiManage · Dr Dris".encode() in response.data
    assert b"All rights reserved" not in response.data
    assert "جميع الحقوق محفوظة".encode() not in response.data
    assert "ResiManage · Dr Dris".encode() in response.data
    assert "✚".encode() not in response.data



def test_android_launcher_has_resimanage_name_and_doctor_icon():
    project_root = Path(__file__).resolve().parents[1]
    manifest = (project_root / "android/app/src/main/AndroidManifest.xml").read_text(
        encoding="utf-8"
    )
    launcher_icon = project_root / "android/app/src/main/res/drawable-nodpi/resimanage_3d_launcher.jpg"
    assert 'android:label="ResiManage"' in manifest
    assert 'android:icon="@drawable/resimanage_3d_launcher"' in manifest
    assert 'android:roundIcon="@drawable/resimanage_3d_launcher"' in manifest
    assert launcher_icon.is_file()


def test_login_and_protected_dashboard(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    response = login(client)
    assert response.status_code == 200
    assert "Résidents".encode() in response.data
    client.get("/logout")
    protected = client.get("/residents")
    assert protected.status_code == 302
    assert "/login" in protected.headers["Location"]


def test_can_add_resident_without_touching_real_database(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    response = client.post(
        "/residents",
        data={"surname": "TestSurname", "firstname": "TestFirst", "year": "2", "phone": "000"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"TestSurname" in response.data
    with rotation_app.db() as conn:
        row = conn.execute("SELECT surname, firstname, year FROM residents WHERE surname=?", ("TestSurname",)).fetchone()
    assert tuple(row) == ("TestSurname", "TestFirst", 2)


def test_seed_has_nineteen_terrains_and_four_periods(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM terrains").fetchone()[0] == 19
        assert conn.execute("SELECT COUNT(*) FROM periods").fetchone()[0] == 4
        optional = {r[0] for r in conn.execute("SELECT name FROM terrains WHERE kind='optional'")}
    assert optional == {"Sédation", "Maxillo-faciale", "CAC DBK", "Brûlés", "Chirurgie cardiaque"}
    assert "Gynécologie" not in optional
    with rotation_app.db() as conn:
        assert conn.execute("SELECT kind FROM terrains WHERE name='Gynécologie'").fetchone()[0] != "optional"
        assert conn.execute("SELECT kind FROM terrains WHERE name='Chirurgie générale'").fetchone()[0] == "mandatory"


def test_assignment_requires_capacity_and_blocks_same_period_duplicate(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    client.get("/lang/ar", headers={"Referer": "http://localhost/"})
    login(client)
    with rotation_app.db() as conn:
        resident_id = conn.execute("SELECT id FROM residents WHERE surname='TestSurname'").fetchone()
        if resident_id is None:
            conn.execute(
                "INSERT INTO residents(surname, firstname, year) VALUES(?,?,?)",
                ("AssignTest", "Resident", 2),
            )
            resident_id = conn.execute("SELECT id FROM residents WHERE surname='AssignTest'").fetchone()
        rid = resident_id[0]
        terrain_id = conn.execute("SELECT id FROM terrains WHERE name='Réanimation chirurgicale'").fetchone()[0]
        second_terrain_id = conn.execute("SELECT id FROM terrains WHERE name='Urologie'").fetchone()[0]
        period_id = conn.execute("SELECT id FROM periods ORDER BY id LIMIT 1").fetchone()[0]
        year_label = conn.execute("SELECT year_label FROM periods WHERE id=?", (period_id,)).fetchone()[0]

    response = client.post(
        "/assign",
        data={"resident": str(rid), "terrain": str(terrain_id), "period": str(period_id)},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "حدّد السعة أولاً".encode() in response.data

    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO capacities(year_label, terrain_id, period_id, places) VALUES(?,?,?,1)",
            (year_label, terrain_id, period_id),
        )

    response = client.post(
        "/assign",
        data={"resident": str(rid), "terrain": str(terrain_id), "period": str(period_id)},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with rotation_app.db() as conn:
        assigned = conn.execute(
            "SELECT status FROM assignments WHERE resident_id=? AND period_id=?",
            (rid, period_id),
        ).fetchone()
    assert assigned is not None
    assert assigned["status"] == "confirmed"

    response = client.post(
        "/assign",
        data={"resident": str(rid), "terrain": str(second_terrain_id), "period": str(period_id)},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with rotation_app.db() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM assignments WHERE resident_id=? AND period_id=?",
            (rid, period_id),
        ).fetchone()[0]
    assert count == 1


def test_capacity_limit_is_enforced_for_two_residents(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    client.get("/lang/ar", headers={"Referer": "http://localhost/"})
    login(client)
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname, firstname, year) VALUES(?,?,?)",
            ("CapacityOne", "Resident", 3),
        )
        conn.execute(
            "INSERT INTO residents(surname, firstname, year) VALUES(?,?,?)",
            ("CapacityTwo", "Resident", 2),
        )
        ids = conn.execute(
            "SELECT id, surname FROM residents WHERE surname IN ('CapacityOne','CapacityTwo')"
        ).fetchall()
        resident_ids = {r["surname"]: r["id"] for r in ids}
        terrain_id = conn.execute("SELECT id FROM terrains WHERE name='Réanimation polyvalente'").fetchone()[0]
        period_id = conn.execute("SELECT id FROM periods ORDER BY id LIMIT 1").fetchone()[0]
        year_label = conn.execute("SELECT year_label FROM periods WHERE id=?", (period_id,)).fetchone()[0]
        conn.execute(
            "INSERT INTO capacities(year_label, terrain_id, period_id, places) VALUES(?,?,?,1)",
            (year_label, terrain_id, period_id),
        )

    first = client.post(
        "/assign",
        data={"resident": str(resident_ids["CapacityOne"]), "terrain": str(terrain_id), "period": str(period_id)},
        follow_redirects=True,
    )
    assert first.status_code == 200
    second = client.post(
        "/assign",
        data={"resident": str(resident_ids["CapacityTwo"]), "terrain": str(terrain_id), "period": str(period_id)},
        follow_redirects=True,
    )
    assert second.status_code == 200
    assert "السعة مكتملة".encode() in second.data
    with rotation_app.db() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM assignments WHERE terrain_id=? AND period_id=? AND status='confirmed'",
            (terrain_id, period_id),
        ).fetchone()[0]
    assert count == 1


def test_repeat_is_blocked_until_all_core_terrains_are_completed(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    client.get("/lang/ar", headers={"Referer": "http://localhost/"})
    login(client)
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname, firstname, year) VALUES(?,?,?)",
            ("RepeatRule", "Resident", 4),
        )
        rid = conn.execute("SELECT id FROM residents WHERE surname='RepeatRule'").fetchone()[0]
        target = conn.execute(
            "SELECT id FROM terrains WHERE name='Réanimation chirurgicale'"
        ).fetchone()[0]
        period_id = conn.execute("SELECT id FROM periods ORDER BY id LIMIT 1").fetchone()[0]
        year_label = conn.execute("SELECT year_label FROM periods WHERE id=?", (period_id,)).fetchone()[0]
        conn.execute(
            "INSERT INTO capacities(year_label, terrain_id, period_id, places) VALUES(?,?,?,2)",
            (year_label, target, period_id),
        )
        conn.execute(
            "INSERT INTO history(resident_id, terrain_id, year_label, period, date_done) VALUES(?,?,?,?,?)",
            (rid, target, "2025-2026", "01 Fév - 30 Avr", "2026-04-30"),
        )

    with rotation_app.app.test_request_context("/"):
        with rotation_app.db() as conn:
            allowed, message, status = rotation_app.check(conn, rid, target, period_id, year_label)
            assert allowed is False
            assert "Stage déjà effectué" in message

    with rotation_app.db() as conn:
        conn.execute(
            """
            INSERT INTO history(resident_id, terrain_id, year_label, period, date_done)
            SELECT ?, id, '2025-2026', 'historique', '2026-04-30'
            FROM terrains
            WHERE kind IN ('mandatory', 'basic')
              AND id NOT IN (SELECT terrain_id FROM history WHERE resident_id=?)
            """,
            (rid, rid),
        )

    with rotation_app.app.test_request_context("/"):
        with rotation_app.db() as conn:
            allowed, message, status = rotation_app.check(conn, rid, target, period_id, year_label)
    assert allowed is True
    assert status == "confirmed"
    assert "Répétition autorisée" in message

def test_resident_profile_and_objectives_are_saved_and_audited(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname, firstname, year) VALUES(?,?,?)", ("Profile", "Resident", 2))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Profile'").fetchone()[0]
        terrain_id = conn.execute("SELECT id FROM terrains WHERE name='Réanimation chirurgicale'").fetchone()[0]
    response = client.post("/profile/" + str(rid), data={
        "birth_place": "Tizi Ouzou", "birth_date": "1998-05-02",
        "phone": "0550000000", "photo_path": ""
    }, follow_redirects=True)
    assert response.status_code == 200
    with rotation_app.db() as conn:
        row = conn.execute("SELECT birth_place,birth_date,phone FROM residents WHERE id=?", (rid,)).fetchone()
        assert tuple(row) == ("Tizi Ouzou", "1998-05-02", "0550000000")
    response = client.post("/objectives", data={
        "terrain": str(terrain_id), "study_year": "2", "objective": "Manage airway safely"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Manage airway safely" in response.data
    with rotation_app.db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE action='resident.profile_updated'").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM objectives WHERE objective='Manage airway safely'").fetchone()[0] == 1


def test_first_year_progression_requires_every_component_at_least_ten(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,1)", ("Pass", "Resident"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Pass'").fetchone()[0]
    for module, theory, practical in [("Module A", 12, 11), ("Module B", 10, 10)]:
        client.post("/exams", data={"action":"record","resident":str(rid),"study_year":"1","module":module,"theory":str(theory),"practical":str(practical)})
    client.post("/exams", data={"action":"evaluate_first_year","resident":str(rid),"study_year":"1","all_modules_confirmed":"yes"})
    with rotation_app.db() as conn:
        assert conn.execute("SELECT year FROM residents WHERE id=?", (rid,)).fetchone()[0] == 2
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,1)", ("Fail", "Resident"))
        fail_id = conn.execute("SELECT id FROM residents WHERE surname='Fail'").fetchone()[0]
    for module, theory, practical in [("Module A", 15, 15), ("Module B", 9, 16)]:
        client.post("/exams", data={"action":"record","resident":str(fail_id),"study_year":"1","module":module,"theory":str(theory),"practical":str(practical)})
    client.post("/exams", data={"action":"evaluate_first_year","resident":str(fail_id),"study_year":"1","all_modules_confirmed":"yes"})
    with rotation_app.db() as conn:
        assert conn.execute("SELECT year FROM residents WHERE id=?", (fail_id,)).fetchone()[0] == 1


def test_first_year_progression_does_not_advance_inactive_resident(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,1,'inactive')",
            ("InactivePass", "Resident"),
        )
        rid = conn.execute(
            "SELECT id FROM residents WHERE surname='InactivePass'"
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO exam_records(resident_id,study_year,module,theory,practical) VALUES(?,1,?,?,?)",
            (rid, "Module A", 12, 12),
        )
        conn.commit()

    response = client.post(
        "/exams",
        data={
            "action": "evaluate_first_year",
            "resident": str(rid),
            "study_year": "1",
            "all_modules_confirmed": "yes",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Le résident est inactif".encode() in response.data
    with rotation_app.db() as conn:
        resident = conn.execute(
            "SELECT year,status FROM residents WHERE id=?", (rid,)
        ).fetchone()
        assert (resident["year"], resident["status"]) == (1, "inactive")
        assert conn.execute(
            "SELECT COUNT(*) FROM audit WHERE action='resident.year_advanced' AND details LIKE ?",
            (f"%resident_id={rid};%",),
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM decisions WHERE details LIKE ?",
            ("%InactivePass Resident — first-year exams%",),
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM audit WHERE action='exam.first_year_evaluated' AND details LIKE ?",
            (f"%resident_id={rid};%",),
        ).fetchone()[0] == 0


def test_dems_archive_keeps_resident_and_history(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    for username in ("benhocine", "drdris"):
        client.post("/users", data={"username": username, "password": "strong-test-password-2026", "role": "super_admin"}, follow_redirects=True)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,4)", ("Graduate", "Resident"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Graduate'").fetchone()[0]
        tid = conn.execute("SELECT id FROM terrains WHERE name='Urologie'").fetchone()[0]
        conn.execute("INSERT INTO history(resident_id,terrain_id,year_label,period,date_done) VALUES(?,?,?,?,?)",
                     (rid, tid, "2025-2026", "01 Mai - 30 Juillet", "2025-07-30"))
        conn.commit()

    with client.session_transaction() as sess:
        sess["user"] = "benhocine"
        sess["role"] = "super_admin"
    first_vote = client.post("/dems", data={"resident":str(rid),"success_date":"2026-10-01","outcome":"approve","reason":"DEMS passed"}, follow_redirects=True)
    assert first_vote.status_code == 200
    with rotation_app.db() as conn:
        assert conn.execute("SELECT status FROM residents WHERE id=?", (rid,)).fetchone()[0] == "active"
        assert conn.execute("SELECT COUNT(*) FROM dems_archive WHERE resident_id=?", (rid,)).fetchone()[0] == 0

    with client.session_transaction() as sess:
        sess["user"] = "drdris"
        sess["role"] = "super_admin"
    second_vote = client.post("/dems", data={"resident":str(rid),"success_date":"2026-10-01","outcome":"approve","reason":"Reviewed and approved"}, follow_redirects=True)
    assert second_vote.status_code == 200
    with rotation_app.db() as conn:
        row = conn.execute("SELECT status,dems_status FROM residents WHERE id=?", (rid,)).fetchone()
        assert tuple(row) == ("graduated", "success")
        assert conn.execute("SELECT COUNT(*) FROM history WHERE resident_id=?", (rid,)).fetchone()[0] == 1
        archive = conn.execute("SELECT history_json FROM dems_archive WHERE resident_id=?", (rid,)).fetchone()
        assert "Urologie" in archive["history_json"]
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE action='dems.vote_recorded'").fetchone()[0] == 2


def test_standard_user_cannot_access_super_admin_pages(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    response = client.post("/users", data={
        "username":"ordinary-user","password":"ordinary-password-2026","role":"user"
    }, follow_redirects=True)
    assert response.status_code == 200
    client.get("/logout")
    response = client.post("/login", data={
        "username":"ordinary-user","password":"ordinary-password-2026"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert client.get("/settings").status_code == 403
    assert client.get("/dems").status_code == 403
    assert client.get("/audit").status_code == 403

def test_standard_user_cannot_create_residents(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    client.post(
        "/users",
        data={
            "username": "standard-operator",
            "password": "standard-operator-password-2026",
            "role": "user",
        },
        follow_redirects=True,
    )
    with client.session_transaction() as sess:
        sess["user"] = "standard-operator"
        sess["role"] = "user"

    response = client.post(
        "/residents",
        data={
            "surname": "Unauthorized",
            "firstname": "Resident",
            "year": "2",
            "phone": "",
        },
        follow_redirects=False,
    )
    assert response.status_code == 403
    with rotation_app.db() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM residents WHERE surname='Unauthorized'"
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM audit WHERE action='resident.created' AND details='Unauthorized Resident'"
        ).fetchone()[0] == 0


def test_standard_user_cannot_record_or_change_exam_marks(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    client.post(
        "/users",
        data={
            "username": "exam-operator",
            "password": "exam-operator-password-2026",
            "role": "user",
        },
        follow_redirects=True,
    )
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES(?,?,1)",
            ("ProtectedExam", "Resident"),
        )
        rid = conn.execute(
            "SELECT id FROM residents WHERE surname='ProtectedExam'"
        ).fetchone()[0]
        conn.commit()
    with client.session_transaction() as sess:
        sess["user"] = "exam-operator"
        sess["role"] = "user"

    response = client.post(
        "/exams",
        data={
            "action": "record",
            "resident": str(rid),
            "study_year": "1",
            "module": "Unauthorized module",
            "theory": "20",
            "practical": "20",
        },
        follow_redirects=False,
    )
    assert response.status_code == 403
    with rotation_app.db() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM exam_records WHERE resident_id=?", (rid,)
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM audit WHERE action='exam.recorded'"
        ).fetchone()[0] == 0


def test_backup_and_restore_preserve_database_and_resident_photos(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    photo_dir = tmp_path / "resident_photos"
    photo_dir.mkdir(exist_ok=True)
    photo_path = photo_dir / "test-resident.webp"
    photo_path.write_bytes(b"original-photo-bytes")
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,?)", ("BeforeBackup", "Resident", 2))
    backup_response = client.get("/backup")
    assert backup_response.status_code == 200
    assert backup_response.mimetype == "application/zip"
    backup_bytes = backup_response.get_data()
    with zipfile.ZipFile(io.BytesIO(backup_bytes)) as bundle:
        assert "rotation.db" in bundle.namelist()
        assert "resident_photos/test-resident.webp" in bundle.namelist()
        assert bundle.read("resident_photos/test-resident.webp") == b"original-photo-bytes"
    open_conn = rotation_app.db()
    open_conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,?)", ("AddedAfterBackup", "Resident", 1))
    open_conn.commit()  # Keep an idle SQLite handle open across restore to cover Windows.
    photo_path.write_bytes(b"changed-photo-bytes")
    restored = client.post("/restore", data={
        "backup_file": (io.BytesIO(backup_bytes), "resimanage_full_backup.zip")
    }, content_type="multipart/form-data", follow_redirects=True)
    assert restored.status_code == 200
    assert b"Restore completed." in restored.data, restored.data.decode("utf-8", errors="replace")
    with rotation_app.db() as restored_conn:
        assert restored_conn.execute("SELECT COUNT(*) FROM residents WHERE surname='BeforeBackup'").fetchone()[0] == 1
        assert restored_conn.execute("SELECT COUNT(*) FROM residents WHERE surname='AddedAfterBackup'").fetchone()[0] == 0
        assert restored_conn.execute("SELECT COUNT(*) FROM audit WHERE action='database.restored'").fetchone()[0] == 1
    assert open_conn.execute("SELECT COUNT(*) FROM residents WHERE surname='AddedAfterBackup'").fetchone()[0] == 0
    open_conn.close()
    assert (tmp_path / "resident_photos" / "test-resident.webp").read_bytes() == b"original-photo-bytes"
    assert list(tmp_path.glob("rotation_backup_before_restore_*.db"))
    assert list(tmp_path.glob("rotation_backup_before_restore_*.zip"))

def test_csv_import_requires_preview_and_does_not_invent_history(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    source = b"surname,firstname,year,phone\nImportSurname,ImportFirst,3,0551234567\n"
    preview = client.post("/import", data={
        "file": (io.BytesIO(source), "residents.csv")
    }, content_type="multipart/form-data", follow_redirects=True)
    assert preview.status_code == 200, preview.data.decode("utf-8", errors="replace")
    assert b"ImportSurname" in preview.data, preview.data.decode("utf-8", errors="replace")
    match = re.search(rb'name="preview_id" value="(\d+)"', preview.data)
    assert match
    confirmed = client.post("/import", data={
        "action":"confirm", "preview_id":match.group(1).decode()
    }, follow_redirects=True)
    assert confirmed.status_code == 200
    with rotation_app.db() as conn:
        rid = conn.execute("SELECT id FROM residents WHERE surname='ImportSurname'").fetchone()[0]
        assert conn.execute("SELECT COUNT(*) FROM history WHERE resident_id=?", (rid,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE action='residents.imported'").fetchone()[0] == 1

def test_mandatory_year_override_requires_reason_and_records_audit(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,2)", ("Override", "Resident"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Override'").fetchone()[0]
        conn.execute("INSERT INTO terrains(name,kind,mandatory_year) VALUES(?,?,3)", ("Year Three Only", "mandatory"))
        tid = conn.execute("SELECT id FROM terrains WHERE name='Year Three Only'").fetchone()[0]
        period_id = conn.execute("SELECT id FROM periods ORDER BY id LIMIT 1").fetchone()[0]
        year_label = conn.execute("SELECT year_label FROM periods WHERE id=?", (period_id,)).fetchone()[0]
        conn.execute("INSERT INTO capacities(year_label,terrain_id,period_id,places) VALUES(?,?,?,1)", (year_label,tid,period_id))
    response = client.post("/assign", data={"resident":str(rid),"terrain":str(tid),"period":str(period_id)}, follow_redirects=True)
    assert response.status_code == 200
    with rotation_app.db() as conn:
        aid = conn.execute("SELECT id FROM assignments WHERE resident_id=? AND status='pending'", (rid,)).fetchone()[0]
    client.post("/decisions", data={"aid":str(aid),"outcome":"approve","reason":"Authorized educational exception"}, follow_redirects=True)
    with rotation_app.db() as conn:
        assert conn.execute("SELECT status FROM assignments WHERE id=?", (aid,)).fetchone()[0] == "confirmed"
        assert conn.execute("SELECT COUNT(*) FROM decisions WHERE reason='Authorized educational exception'").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE action='assignment.override_approved'").fetchone()[0] == 1


def test_uploaded_resident_photo_is_stored_and_served_safely(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,1)", ("Photo", "Resident"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Photo'").fetchone()[0]
    from PIL import Image
    image = Image.new("RGB", (8, 8), (30, 120, 180))
    image_buffer = io.BytesIO()
    image.save(image_buffer, format="PNG")
    png = image_buffer.getvalue()
    response = client.post("/profile/" + str(rid), data={
        "birth_place":"", "birth_date":"", "phone":"",
        "photo":(io.BytesIO(png),"portrait.png")
    }, content_type="multipart/form-data", follow_redirects=True)
    assert response.status_code == 200
    with rotation_app.db() as conn:
        path = conn.execute("SELECT photo_path FROM residents WHERE id=?", (rid,)).fetchone()[0]
    assert path.startswith("/photos/resident_")
    photo_response = client.get(path)
    assert photo_response.status_code == 200
    assert photo_response.data.startswith(b"\x89PNG")

def test_assignment_resident_choices_are_sorted_by_year_priority(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,1)", ("FirstYear", "Resident"))
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,3)", ("ThirdYear", "Resident"))
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,4)", ("FourthYear", "Resident"))
    response = client.get("/assign")
    html = response.data.decode("utf-8")
    assert html.index("FourthYear") < html.index("ThirdYear") < html.index("FirstYear")


def test_academic_year_change_creates_four_new_periods_and_preserves_old_periods(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        old_year = conn.execute("SELECT year_label FROM periods ORDER BY id LIMIT 1").fetchone()[0]
    response = client.post("/settings", data={
        "lang":"fr","year":"2027-2028","director":"Dr Dris","new_password":""
    }, follow_redirects=True)
    assert response.status_code == 200
    with rotation_app.db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM periods WHERE year_label='2027-2028'").fetchone()[0] == 4
        assert conn.execute("SELECT COUNT(*) FROM periods WHERE year_label=?", (old_year,)).fetchone()[0] == 4


def test_xlsx_import_preview(tmp_path, monkeypatch):
    from openpyxl import Workbook
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Nom","Prénom","Année","Téléphone"])
    sheet.append(["ExcelResident","ExcelFirst",2,"0551111111"])
    stream = io.BytesIO()
    workbook.save(stream)
    stream.seek(0)
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    preview = client.post("/import", data={"file":(stream,"residents.xlsx")},
                          content_type="multipart/form-data", follow_redirects=True)
    assert preview.status_code == 200
    assert b"ExcelResident" in preview.data, preview.data.decode("utf-8", errors="replace")

def test_docx_import_reads_table_headers_and_resident_rows(tmp_path, monkeypatch):
    from docx import Document
    document = Document()
    table = document.add_table(rows=1, cols=3)
    table.rows[0].cells[0].text = "Nom"
    table.rows[0].cells[1].text = "Prénom"
    table.rows[0].cells[2].text = "Année"
    row = table.add_row().cells
    row[0].text = "WordResident"
    row[1].text = "WordFirst"
    row[2].text = "4"
    stream = io.BytesIO()
    document.save(stream)
    stream.seek(0)
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    preview = client.post("/import", data={"file":(stream,"residents.docx")},
                          content_type="multipart/form-data", follow_redirects=True)
    assert preview.status_code == 200
    assert b"WordResident" in preview.data


def test_csv_export_includes_exam_objective_archive_and_audit_tables_but_not_users(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    response = client.get("/export")
    assert response.status_code == 200
    content = response.get_data().decode("utf-8-sig")
    for table in ("exam_records", "objectives", "dems_archive", "leave_years", "leave_entries", "external_rotations", "promotion_votes", "dems_votes", "audit"):
        assert table in content
    assert "users" not in content
    assert "password_hash" not in content

def test_fresh_database_requires_admin_to_set_a_private_password(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    monkeypatch.delenv("ROTATION_INITIAL_PASSWORD", raising=False)
    page = client.get("/login")
    assert page.status_code == 200
    assert b"confirm_password" in page.data
    response = client.post("/login", data={
        "username":"admin",
        "password":"fresh-private-password-2026",
        "confirm_password":"fresh-private-password-2026"
    }, follow_redirects=True)
    assert response.status_code == 200
    with rotation_app.db() as conn:
        stored = conn.execute("SELECT value FROM settings WHERE key='password'").fetchone()[0]
        user = conn.execute("SELECT role,password_hash FROM users WHERE username='admin'").fetchone()
    assert stored.startswith("pbkdf2_sha256$")
    assert user["role"] == "super_admin"
    assert user["password_hash"].startswith("pbkdf2_sha256$")


def test_legacy_password_hash_is_upgraded_after_successful_login(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    client.get("/login")
    with rotation_app.app.test_request_context("/"):
        with rotation_app.db() as conn:
            conn.execute("UPDATE settings SET value=? WHERE key='password'",
                         (hashlib.sha256(b"legacy-test-password-2026").hexdigest(),))
    response = client.post("/login", data={
        "username":"admin","password":"legacy-test-password-2026"
    }, follow_redirects=True)
    assert response.status_code == 200
    with rotation_app.db() as conn:
        stored = conn.execute("SELECT value FROM settings WHERE key='password'").fetchone()[0]
        user = conn.execute("SELECT password_hash,role FROM users WHERE username='admin'").fetchone()
    assert stored.startswith("pbkdf2_sha256$")
    assert user["password_hash"].startswith("pbkdf2_sha256$")
    assert user["role"] == "super_admin"

def test_terrain_deactivation_preserves_history_and_hides_it_from_new_assignments(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,2)", ("TerrainHistory", "Resident"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='TerrainHistory'").fetchone()[0]
        tid = conn.execute("SELECT id FROM terrains WHERE name='Urologie'").fetchone()[0]
        conn.execute("INSERT INTO history(resident_id,terrain_id,year_label,period,date_done) VALUES(?,?,?,?,?)",
                     (rid,tid,"2025-2026","01 Mai - 30 Juillet","2025-07-30"))
    response = client.post("/terrains", data={"action":"deactivate","tid":str(tid)}, follow_redirects=True)
    assert response.status_code == 200
    with rotation_app.db() as conn:
        assert conn.execute("SELECT active FROM terrains WHERE id=?", (tid,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM history WHERE resident_id=? AND terrain_id=?", (rid,tid)).fetchone()[0] == 1
    assert b"Urologie" not in client.get("/assign").data


def test_assignment_cancellation_is_audited_and_does_not_delete_record(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,3)", ("Cancel", "Resident"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Cancel'").fetchone()[0]
        tid = conn.execute("SELECT id FROM terrains WHERE name='Urologie'").fetchone()[0]
        pid = conn.execute("SELECT id FROM periods ORDER BY id LIMIT 1").fetchone()[0]
        conn.execute("INSERT INTO assignments(resident_id,terrain_id,period_id,status) VALUES(?,?,?,'confirmed')",(rid,tid,pid))
        aid = conn.execute("SELECT id FROM assignments WHERE resident_id=?", (rid,)).fetchone()[0]
    response = client.post("/assignments/" + str(aid) + "/cancel", follow_redirects=True)
    assert response.status_code == 200
    with rotation_app.db() as conn:
        assert conn.execute("SELECT status FROM assignments WHERE id=?", (aid,)).fetchone()[0] == "cancelled"
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE action='assignment.cancelled'").fetchone()[0] == 1


def test_user_deactivation_is_audited_and_blocks_login(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    client.post("/users", data={"username":"temporary-user","password":"temporary-user-password-2026","role":"user"})
    with rotation_app.db() as conn:
        uid = conn.execute("SELECT id FROM users WHERE username='temporary-user'").fetchone()[0]
    client.post("/users", data={"action":"deactivate","user_id":str(uid)})
    with rotation_app.db() as conn:
        assert conn.execute("SELECT active FROM users WHERE id=?", (uid,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE action='user.deactivated'").fetchone()[0] == 1
    client.get("/logout")
    response = client.post("/login", data={"username":"temporary-user","password":"temporary-user-password-2026"}, follow_redirects=True)
    assert b"Temporary user" not in response.data
    assert client.get("/settings").status_code == 302


def test_email_registration_requires_verification_code(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    sent = {}
    monkeypatch.setattr(rotation_app, "send_verification_email", lambda recipient, code, lang="fr": sent.update(email=recipient, code=code, lang=lang))
    response = client.get("/register")
    assert response.status_code == 200
    assert b'type="email"' in response.data

    response = client.post("/register", data={
        "username": "emailuser",
        "email": "emailuser@example.com",
        "password": "strong-test-password-2026",
        "confirm_password": "strong-test-password-2026",
    })
    assert response.status_code == 302
    assert response.headers["Location"] == "/verify-email"
    assert sent["email"] == "emailuser@example.com"
    with rotation_app.db() as conn:
        assert conn.execute("SELECT 1 FROM users WHERE username='emailuser'").fetchone() is None
        pending = conn.execute("SELECT attempts FROM pending_registrations WHERE email=?", (sent["email"],)).fetchone()
        assert pending is not None
        assert pending["attempts"] == 0

    wrong = client.post("/verify-email", data={"code": "000000"})
    assert wrong.status_code == 200
    with rotation_app.db() as conn:
        assert conn.execute("SELECT 1 FROM users WHERE username='emailuser'").fetchone() is None

    verified = client.post("/verify-email", data={"code": sent["code"]})
    assert verified.status_code == 302
    assert verified.headers["Location"] == "/login"
    with rotation_app.db() as conn:
        account = conn.execute("SELECT username,email,email_verified,role FROM users WHERE username='emailuser'").fetchone()
        assert tuple(account) == ("emailuser", "emailuser@example.com", 1, "user")
        assert conn.execute("SELECT 1 FROM pending_registrations WHERE email=?", (sent["email"],)).fetchone() is None


def test_annual_leave_records_days_and_carries_unused_balance(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,?,?)", ("Leave", "Test", 2, "active"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Leave'").fetchone()[0]
        conn.commit()
    from datetime import date, timedelta
    start = date.today().replace(month=1, day=1)
    end = start + timedelta(days=4)
    response = client.post("/leave", data={
        "resident_id": str(rid), "start_date": start.isoformat(),
        "end_date": end.isoformat(), "notes": "test leave"
    }, follow_redirects=True)
    assert response.status_code == 200
    with rotation_app.db() as conn:
        entry = conn.execute("SELECT days FROM leave_entries WHERE resident_id=?", (rid,)).fetchone()
        assert entry[0] == 5
        earned = conn.execute("SELECT SUM(earned_days) FROM leave_years WHERE resident_id=?", (rid,)).fetchone()[0]
        used = conn.execute("SELECT SUM(days) FROM leave_entries WHERE resident_id=?", (rid,)).fetchone()[0]
        assert earned >= 30
        assert earned - used >= 25


def test_external_rotation_blocks_overlapping_local_period(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,?,?)", ("Away", "Resident", 2, "active"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Away'").fetchone()[0]
        tid = conn.execute("SELECT id FROM terrains WHERE name='Réanimation chirurgicale'").fetchone()[0]
        period = conn.execute("SELECT id,year_label,name FROM periods WHERE name='Période 3'").fetchone()
        if period is None:
            period = conn.execute("SELECT id,year_label,name FROM periods ORDER BY id LIMIT 1").fetchone()
        conn.execute("INSERT INTO external_rotations(resident_id,supervisor,destination,hospital,country,rotation_type,start_date,end_date,status) VALUES(?,?,?,?,?,?,?,?,?)",
                     (rid, "Dr Test", "Paris", "CHU Test", "France", "Observation", "2026-08-01", "2026-10-30", "active"))
        conn.commit()
        allowed, message, status = rotation_app.check(conn, rid, tid, period["id"], period["year_label"])
        assert allowed is False
        assert "External rotation" in message


def test_external_rotation_form_requires_all_destination_details(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,?,?)", ("Trip", "Resident", 3, "active"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Trip'").fetchone()[0]
        conn.commit()
    response = client.post("/external-rotations", data={
        "resident_id": str(rid), "supervisor": "Dr Test", "destination": "Paris",
        "hospital": "CHU Test", "country": "France", "rotation_type": "Observation",
        "start_date": "2026-11-01", "end_date": "2026-12-01", "notes": "test"
    }, follow_redirects=True)
    assert response.status_code == 200
    with rotation_app.db() as conn:
        row = conn.execute("SELECT supervisor,hospital,country,rotation_type FROM external_rotations WHERE resident_id=?", (rid,)).fetchone()
        assert tuple(row) == ("Dr Test", "CHU Test", "France", "Observation")

def test_leave_carries_unused_days_forward_and_blocks_overdraw(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,?,?)", ("Carry", "Leave", 2, "active"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Carry'").fetchone()[0]
        conn.commit()

    first = client.post("/leave", data={"resident_id": rid, "start_date": "2024-01-01", "end_date": "2024-01-10"}, follow_redirects=True)
    assert first.status_code == 200
    second = client.post("/leave", data={"resident_id": rid, "start_date": "2025-01-01", "end_date": "2025-01-25"}, follow_redirects=True)
    assert second.status_code == 200
    with rotation_app.db() as conn:
        years = conn.execute("SELECT SUM(earned_days) FROM leave_years WHERE resident_id=? AND year IN (2024,2025)", (rid,)).fetchone()[0]
        used = conn.execute("SELECT SUM(days) FROM leave_entries WHERE resident_id=?", (rid,)).fetchone()[0]
    assert years == 60
    assert used == 35
    rejected = client.post("/leave", data={"resident_id": rid, "start_date": "2025-02-01", "end_date": "2025-02-26"}, follow_redirects=True)
    assert rejected.status_code == 200
    assert b"Insufficient accrued leave balance" in rejected.data
    with rotation_app.db() as conn:
        assert conn.execute("SELECT SUM(days) FROM leave_entries WHERE resident_id=?", (rid,)).fetchone()[0] == 35


def test_leave_rejects_overlapping_entries(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,?,?)", ("Overlap", "Leave", 1, "active"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Overlap'").fetchone()[0]
        conn.commit()
    client.post("/leave", data={"resident_id": rid, "start_date": "2026-01-01", "end_date": "2026-01-10"}, follow_redirects=True)
    rejected = client.post("/leave", data={"resident_id": rid, "start_date": "2026-01-05", "end_date": "2026-01-12"}, follow_redirects=True)
    assert rejected.status_code == 200
    assert b"Leave dates overlap an existing entry" in rejected.data
    with rotation_app.db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM leave_entries WHERE resident_id=?", (rid,)).fetchone()[0] == 1


def test_external_rotation_returned_record_still_blocks_overlapping_period(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,?,?)", ("Returned", "Away", 2, "active"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Returned'").fetchone()[0]
        tid = conn.execute("SELECT id FROM terrains WHERE name='Réanimation chirurgicale'").fetchone()[0]
        period = conn.execute("SELECT id,year_label,name FROM periods WHERE name='Période 3'").fetchone()
        assert period is not None
        conn.execute("INSERT INTO external_rotations(resident_id,supervisor,destination,hospital,country,rotation_type,start_date,end_date,status) VALUES(?,?,?,?,?,?,?,?,?)",
                     (rid, "Dr Test", "Paris", "CHU Test", "France", "Observation", "2026-08-01", "2026-10-30", "returned"))
        conn.commit()
        allowed, message, _ = rotation_app.check(conn, rid, tid, period["id"], period["year_label"])
    assert allowed is False
    assert "External rotation" in message


def test_assignment_resident_options_mark_external_period_conflicts(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,?,?)", ("Blocked", "Resident", 2, "active"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Blocked'").fetchone()[0]
        period = conn.execute("SELECT id FROM periods WHERE name='Période 3'").fetchone()
        assert period is not None
        conn.execute("INSERT INTO external_rotations(resident_id,supervisor,destination,hospital,country,rotation_type,start_date,end_date,status) VALUES(?,?,?,?,?,?,?,?,?)",
                     (rid, "Dr Test", "Paris", "CHU Test", "France", "Observation", "2026-08-01", "2026-10-30", "returned"))
        conn.commit()
    response = client.get("/assign")
    assert response.status_code == 200
    assert f'data-blocked-periods="{period["id"]}"'.encode() in response.data
    assert b"o.disabled=blocked" in response.data


def test_external_rotation_can_be_edited_and_cancelled_with_audit(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,?,?)", ("Edit", "External", 3, "active"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Edit'").fetchone()[0]
        conn.execute("INSERT INTO external_rotations(resident_id,supervisor,destination,hospital,country,rotation_type,start_date,end_date,status) VALUES(?,?,?,?,?,?,?,?,?)",
                     (rid, "Dr Old", "Paris", "CHU Old", "France", "Observation", "2026-11-01", "2026-12-01", "active"))
        xid = conn.execute("SELECT id FROM external_rotations WHERE resident_id=?", (rid,)).fetchone()[0]
        conn.commit()
    edit = client.post(f"/external-rotations/{xid}/edit", data={
        "resident_id": str(rid), "supervisor": "Dr New", "destination": "Lyon",
        "hospital": "CHU New", "country": "France", "rotation_type": "Clinical",
        "start_date": "2026-11-10", "end_date": "2026-12-10", "notes": "updated"
    }, follow_redirects=True)
    assert edit.status_code == 200
    with rotation_app.db() as conn:
        row = conn.execute("SELECT supervisor,destination,hospital,rotation_type,status FROM external_rotations WHERE id=?", (xid,)).fetchone()
        assert tuple(row) == ("Dr New", "Lyon", "CHU New", "Clinical", "active")
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE action='external_rotation.updated'").fetchone()[0] == 1
    cancelled = client.post(f"/external-rotations/{xid}/cancel", follow_redirects=True)
    assert cancelled.status_code == 200
    with rotation_app.db() as conn:
        assert conn.execute("SELECT status FROM external_rotations WHERE id=?", (xid,)).fetchone()[0] == "cancelled"
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE action='external_rotation.cancelled'").fetchone()[0] == 1

def test_post_without_csrf_token_is_rejected(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    client.get("/login")
    response = client.open("/login", method="POST", data={"username": "admin", "password": "not-a-real-password"})
    assert response.status_code == 400
    assert b"Invalid or missing CSRF token" in response.data


def test_official_admin_accounts_must_be_super_admin_and_cannot_be_disabled(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    for username in ("benhocine", "drdris"):
        invalid = client.post("/users", data={
            "username": username, "password": "strong-test-password-2026", "role": "user"
        }, follow_redirects=True)
        assert invalid.status_code == 200
        assert b"Official accounts must be Super Admins" in invalid.data
        with rotation_app.db() as conn:
            assert conn.execute("SELECT 1 FROM users WHERE lower(username)=?", (username,)).fetchone() is None

        created = client.post("/users", data={
            "username": username, "password": "strong-test-password-2026", "role": "super_admin"
        }, follow_redirects=True)
        assert created.status_code == 200
        with rotation_app.db() as conn:
            row = conn.execute("SELECT id,role,active FROM users WHERE lower(username)=?", (username,)).fetchone()
            assert tuple(row[1:]) == ("super_admin", 1)
            uid = row["id"]
        deactivated = client.post("/users", data={"action": "deactivate", "user_id": str(uid)}, follow_redirects=True)
        assert deactivated.status_code == 200
        assert b"Official accounts cannot be deactivated" in deactivated.data
        with rotation_app.db() as conn:
            assert conn.execute("SELECT active FROM users WHERE id=?", (uid,)).fetchone()[0] == 1

def test_year_progression_requires_approval_from_both_official_admins(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    for username in ("benhocine", "drdris"):
        client.post("/users", data={"username": username, "password": "strong-test-password-2026", "role": "super_admin"}, follow_redirects=True)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,2,'active')", ("Promotion", "Resident"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Promotion'").fetchone()[0]
        conn.commit()

    unauthorized = client.post("/exams", data={"action":"approve_advance","resident":str(rid),"study_year":"2","outcome":"approve","reason":"ok"}, follow_redirects=False)
    assert unauthorized.status_code == 403

    with client.session_transaction() as sess:
        sess["user"] = "benhocine"
        sess["role"] = "super_admin"
    first = client.post("/exams", data={"action":"approve_advance","resident":str(rid),"study_year":"2","outcome":"approve","reason":"First official approves"}, follow_redirects=True)
    assert first.status_code == 200
    with rotation_app.db() as conn:
        assert conn.execute("SELECT year FROM residents WHERE id=?", (rid,)).fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM promotion_votes WHERE resident_id=?", (rid,)).fetchone()[0] == 1

    with client.session_transaction() as sess:
        sess["user"] = "drdris"
        sess["role"] = "super_admin"
    second = client.post("/exams", data={"action":"approve_advance","resident":str(rid),"study_year":"2","outcome":"approve","reason":"Second official approves"}, follow_redirects=True)
    assert second.status_code == 200
    with rotation_app.db() as conn:
        assert conn.execute("SELECT year FROM residents WHERE id=?", (rid,)).fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM promotion_votes WHERE resident_id=?", (rid,)).fetchone()[0] == 0
        decision = conn.execute("SELECT decision,actor FROM decisions WHERE details LIKE '%Promotion Resident — year 2%'").fetchone()
        assert decision["decision"] == "Approved by both official administrators"
        assert decision["actor"] == "benhocine+drdris"


def test_year_progression_is_not_approved_if_either_official_rejects(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    for username in ("benhocine", "drdris"):
        client.post("/users", data={"username": username, "password": "strong-test-password-2026", "role": "super_admin"}, follow_redirects=True)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,3,'active')", ("Reject", "Resident"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Reject'").fetchone()[0]
        conn.commit()
    for username,outcome in (("benhocine","approve"),("drdris","reject")):
        with client.session_transaction() as sess:
            sess["user"] = username
            sess["role"] = "super_admin"
        response = client.post("/exams", data={"action":"approve_advance","resident":str(rid),"study_year":"3","outcome":outcome,"reason":username+" reviewed"}, follow_redirects=True)
        assert response.status_code == 200
    with rotation_app.db() as conn:
        assert conn.execute("SELECT year FROM residents WHERE id=?", (rid,)).fetchone()[0] == 3
        decision = conn.execute("SELECT decision FROM decisions WHERE details LIKE '%Reject Resident — year 3%'").fetchone()
        assert decision[0] == "Rejected by official vote"



def test_dems_archive_is_blocked_if_either_official_rejects(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    for username in ("benhocine", "drdris"):
        client.post("/users", data={
            "username": username,
            "password": "strong-test-password-2026",
            "role": "super_admin",
        }, follow_redirects=True)
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,4,'active')",
            ("DEMSReject", "Resident"),
        )
        rid = conn.execute(
            "SELECT id FROM residents WHERE surname='DEMSReject'"
        ).fetchone()[0]
        conn.commit()

    for username, outcome in (("benhocine", "approve"), ("drdris", "reject")):
        with client.session_transaction() as sess:
            sess["user"] = username
            sess["role"] = "super_admin"
        response = client.post("/dems", data={
            "resident": str(rid),
            "success_date": "2026-10-15",
            "outcome": outcome,
            "reason": username + " reviewed the DEMS result",
        }, follow_redirects=True)
        assert response.status_code == 200

    with rotation_app.db() as conn:
        resident = conn.execute(
            "SELECT status,dems_status FROM residents WHERE id=?", (rid,)
        ).fetchone()
        assert tuple(resident) == ("active", "")
        assert conn.execute(
            "SELECT COUNT(*) FROM dems_archive WHERE resident_id=?", (rid,)
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM dems_votes WHERE resident_id=?", (rid,)
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM audit WHERE action='dems.vote_rejected'"
        ).fetchone()[0] == 1
        decision = conn.execute(
            "SELECT decision FROM decisions WHERE details LIKE '%DEMSReject Resident — DEMS%'"
        ).fetchone()
        assert decision is not None
        assert decision["decision"] == "Not approved by official vote"


def test_assignment_page_has_priority_filters_and_clear_conflict_feedback(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    client.get("/lang/ar", headers={"Referer": "http://localhost/"})
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,?,?)", ("Priority", "Four", 4, "active"))
        conn.execute("INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,?,?)", ("Search", "One", 1, "active"))
        conn.commit()
    response = client.get("/assign")
    assert response.status_code == 200
    assert b'id="assignment-search"' in response.data
    assert b'id="assignment-year-filter"' in response.data
    assert b'value="4"' in response.data and ("السنة".encode() in response.data or b'Year 4' in response.data)
    assert "تخطيط التربصات وتعيين المقيمين".encode() in response.data or b'Rotation planning &amp; resident assignment' in response.data or b'Rotation planning & resident assignment' in response.data
    assert b'rt-assignment-stats' in response.data
    assert b'rt-assignment-notice' in response.data
    assert 'تعارض تربص خارجي'.encode() in response.data
    assert b'rt-assignment-table' in response.data

def test_inactive_core_terrain_does_not_block_repeat_eligibility(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    client.get("/lang/ar", headers={"Referer": "http://localhost/"})
    login(client)
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES(?,?,4)",
            ("InactiveCore", "Resident"),
        )
        rid = conn.execute(
            "SELECT id FROM residents WHERE surname='InactiveCore'"
        ).fetchone()[0]
        target = conn.execute(
            "SELECT id FROM terrains WHERE name='Réanimation chirurgicale'"
        ).fetchone()[0]
        inactive = conn.execute(
            "SELECT id FROM terrains WHERE name='Urologie'"
        ).fetchone()[0]
        period_id = conn.execute(
            "SELECT id FROM periods ORDER BY id LIMIT 1"
        ).fetchone()[0]
        year_label = conn.execute(
            "SELECT year_label FROM periods WHERE id=?", (period_id,)
        ).fetchone()[0]
        conn.execute("UPDATE terrains SET active=0 WHERE id=?", (inactive,))
        conn.execute(
            "INSERT INTO capacities(year_label,terrain_id,period_id,places) VALUES(?,?,?,2)",
            (year_label, target, period_id),
        )
        conn.execute(
            "INSERT INTO history(resident_id,terrain_id,year_label,period,date_done) VALUES(?,?,?,?,?)",
            (rid, target, year_label, "01 Fév - 30 Avr", "2026-04-30"),
        )
        conn.execute(
            """
            INSERT INTO history(resident_id,terrain_id,year_label,period,date_done)
            SELECT ?, id, ?, 'historique', '2026-04-30'
            FROM terrains
            WHERE active=1 AND kind IN ('mandatory','basic') AND id<>?
            """,
            (rid, year_label, target),
        )

    with rotation_app.app.test_request_context("/"):
        with rotation_app.db() as conn:
            allowed, message, status = rotation_app.check(
                conn, rid, target, period_id, year_label
            )

    assert allowed is True
    assert status == "confirmed"
    assert "Répétition autorisée" in message

def test_pending_assignment_cannot_be_approved_after_terrain_deactivation(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,2)", ("StaleTerrain", "Resident"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='StaleTerrain'").fetchone()[0]
        conn.execute("INSERT INTO terrains(name,kind,mandatory_year) VALUES(?,?,3)", ("Pending Deactivated Terrain", "mandatory"))
        tid = conn.execute("SELECT id FROM terrains WHERE name='Pending Deactivated Terrain'").fetchone()[0]
        period = conn.execute("SELECT id,year_label FROM periods ORDER BY id LIMIT 1").fetchone()
        conn.execute("INSERT INTO capacities(year_label,terrain_id,period_id,places) VALUES(?,?,?,1)", (period["year_label"], tid, period["id"]))
    client.post("/assign", data={"resident":str(rid),"terrain":str(tid),"period":str(period["id"])})
    with rotation_app.db() as conn:
        aid = conn.execute("SELECT id FROM assignments WHERE resident_id=? AND status='pending'", (rid,)).fetchone()[0]
        conn.execute("UPDATE terrains SET active=0 WHERE id=?", (tid,))
    response = client.post("/decisions", data={"aid":str(aid),"outcome":"approve","reason":"Review stale request"}, follow_redirects=True)
    assert response.status_code == 200
    with rotation_app.db() as conn:
        assert conn.execute("SELECT status FROM assignments WHERE id=?", (aid,)).fetchone()[0] == "pending"
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE action='assignment.override_approved'").fetchone()[0] == 0


def test_pending_assignment_cannot_be_approved_during_new_external_overlap(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,2)", ("StaleExternal", "Resident"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='StaleExternal'").fetchone()[0]
        conn.execute("INSERT INTO terrains(name,kind,mandatory_year) VALUES(?,?,3)", ("Pending External Terrain", "mandatory"))
        tid = conn.execute("SELECT id FROM terrains WHERE name='Pending External Terrain'").fetchone()[0]
        period = conn.execute("SELECT id,year_label,name FROM periods ORDER BY id LIMIT 1").fetchone()
        conn.execute("INSERT INTO capacities(year_label,terrain_id,period_id,places) VALUES(?,?,?,1)", (period["year_label"], tid, period["id"]))
    client.post("/assign", data={"resident":str(rid),"terrain":str(tid),"period":str(period["id"])})
    start_day, end_day = rotation_app.rotation_period_bounds(period["year_label"], period["name"])
    with rotation_app.db() as conn:
        aid = conn.execute("SELECT id FROM assignments WHERE resident_id=? AND status='pending'", (rid,)).fetchone()[0]
        conn.execute(
            "INSERT INTO external_rotations(resident_id,supervisor,destination,hospital,country,rotation_type,start_date,end_date,status) VALUES(?,?,?,?,?,?,?,?,?)",
            (rid,"Dr Test","Paris","CHU Test","France","Observation",start_day.isoformat(),end_day.isoformat(),"active"),
        )
    response = client.post("/decisions", data={"aid":str(aid),"outcome":"approve","reason":"Review external conflict"}, follow_redirects=True)
    assert response.status_code == 200
    with rotation_app.db() as conn:
        assert conn.execute("SELECT status FROM assignments WHERE id=?", (aid,)).fetchone()[0] == "pending"
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE action='assignment.override_approved'").fetchone()[0] == 0

def test_legacy_terrain_classification_migrates_once_without_rewriting_later_admin_edits(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    legacy = sqlite3.connect(rotation_app.DB)
    legacy.execute(
        "CREATE TABLE terrains(id INTEGER PRIMARY KEY,name TEXT UNIQUE NOT NULL,kind TEXT DEFAULT 'basic',mandatory_year INTEGER DEFAULT 0,active INTEGER NOT NULL DEFAULT 1)"
    )
    legacy.executemany(
        "INSERT INTO terrains(name,kind) VALUES(?,?)",
        [("Sédation", "basic"), ("Maxillo-faciale", "basic"),
         ("Chirurgie cardiaque", "basic"), ("Brûlés", "basic"),
         ("CAC DBK", "basic"), ("Gynécologie", "optional")],
    )
    legacy.commit()
    legacy.close()

    assert client.get("/login").status_code == 200
    with rotation_app.db() as conn:
        for name in ("Sédation", "Maxillo-faciale", "Chirurgie cardiaque", "Brûlés", "CAC DBK"):
            assert conn.execute("SELECT kind FROM terrains WHERE name=?", (name,)).fetchone()[0] == "optional"
        assert conn.execute("SELECT kind FROM terrains WHERE name='Gynécologie'").fetchone()[0] == "basic"
        assert conn.execute(
            "SELECT value FROM settings WHERE key='terrain_classification_migration_20261017'"
        ).fetchone()[0] == "1"
        conn.execute("UPDATE terrains SET kind='mandatory' WHERE name='Sédation'")
        conn.commit()

    monkeypatch.setattr(rotation_app.app, "_ready", False, raising=False)
    assert client.get("/login").status_code == 200
    with rotation_app.db() as conn:
        assert conn.execute("SELECT kind FROM terrains WHERE name='Sédation'").fetchone()[0] == "mandatory"

def test_settings_rejects_password_shorter_than_twelve_characters(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        before = conn.execute(
            "SELECT password_hash FROM users WHERE username='admin'"
        ).fetchone()[0]
        year = conn.execute("SELECT value FROM settings WHERE key='year'").fetchone()[0]

    response = client.post(
        "/settings",
        data={"lang":"ar","year":year,"director":"","new_password":"weak"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "at least 12 characters".encode() in response.data
    with rotation_app.db() as conn:
        after = conn.execute(
            "SELECT password_hash FROM users WHERE username='admin'"
        ).fetchone()[0]
        assert after == before

def test_external_rotation_creation_rejects_overlap_with_existing_local_assignment(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,2)", ("LocalFirst", "Resident"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='LocalFirst'").fetchone()[0]
        tid = conn.execute("SELECT id FROM terrains WHERE name='Réanimation chirurgicale'").fetchone()[0]
        period = conn.execute("SELECT id,year_label,name FROM periods ORDER BY id LIMIT 1").fetchone()
        conn.execute("INSERT INTO assignments(resident_id,terrain_id,period_id,status) VALUES(?,?,?,'confirmed')", (rid,tid,period["id"]))
        conn.commit()
    start_day, end_day = rotation_app.rotation_period_bounds(period["year_label"], period["name"])
    response = client.post("/external-rotations", data={
        "resident_id":str(rid),"supervisor":"Dr Test","destination":"Paris",
        "hospital":"CHU Test","country":"France","rotation_type":"Observation",
        "start_date":start_day.isoformat(),"end_date":end_day.isoformat(),"notes":"overlap"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "Le stage à l’étranger chevauche une affectation locale existante".encode() in response.data
    with rotation_app.db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM external_rotations WHERE resident_id=?", (rid,)).fetchone()[0] == 0


def test_external_rotation_edit_rejects_overlap_with_existing_local_assignment(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,2)", ("LocalEdit", "Resident"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='LocalEdit'").fetchone()[0]
        tid = conn.execute("SELECT id FROM terrains WHERE name='Réanimation chirurgicale'").fetchone()[0]
        period = conn.execute("SELECT id,year_label,name FROM periods ORDER BY id LIMIT 1").fetchone()
        conn.execute("INSERT INTO assignments(resident_id,terrain_id,period_id,status) VALUES(?,?,?,'confirmed')", (rid,tid,period["id"]))
        conn.commit()
    start_day, end_day = rotation_app.rotation_period_bounds(period["year_label"], period["name"])
    nonoverlap_start = end_day + timedelta(days=1)
    nonoverlap_end = nonoverlap_start + timedelta(days=7)
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO external_rotations(resident_id,supervisor,destination,hospital,country,rotation_type,start_date,end_date,status) VALUES(?,?,?,?,?,?,?,?,?)",
            (rid,"Dr Test","Paris","CHU Test","France","Observation",nonoverlap_start.isoformat(),nonoverlap_end.isoformat(),"returned"),
        )
        xid = conn.execute("SELECT id FROM external_rotations WHERE resident_id=?", (rid,)).fetchone()[0]
    response = client.post(f"/external-rotations/{xid}/edit", data={
        "resident_id":str(rid),"supervisor":"Dr Test","destination":"Paris",
        "hospital":"CHU Test","country":"France","rotation_type":"Observation",
        "start_date":start_day.isoformat(),"end_date":end_day.isoformat(),"notes":"overlap"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "Le stage à l’étranger chevauche une affectation locale existante".encode() in response.data
    with rotation_app.db() as conn:
        row = conn.execute("SELECT start_date,end_date FROM external_rotations WHERE id=?", (xid,)).fetchone()
        assert tuple(row) == (nonoverlap_start.isoformat(), nonoverlap_end.isoformat())

def test_resident_edit_persists_and_cannot_bypass_or_reverse_dems_graduation(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,2,'active')", ("Editable", "Resident"))
        editable = conn.execute("SELECT id FROM residents WHERE surname='Editable'").fetchone()[0]
        conn.execute("INSERT INTO residents(surname,firstname,year,status,dems_status) VALUES(?,?,4,'graduated','success')", ("Graduated", "Resident"))
        graduated = conn.execute("SELECT id FROM residents WHERE surname='Graduated'").fetchone()[0]
        conn.execute("INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,4,'active')", ("Attempt", "Bypass"))
        bypass = conn.execute("SELECT id FROM residents WHERE surname='Attempt'").fetchone()[0]

    saved = client.post("/residents", data={
        "action":"edit","rid":str(editable),"year":"2","repeat_year":"0","status":"inactive"
    }, follow_redirects=True)
    assert saved.status_code == 200
    with rotation_app.db() as conn:
        row = conn.execute("SELECT year,status FROM residents WHERE id=?", (editable,)).fetchone()
        assert tuple(row) == (2,"inactive")

    year_change = client.post("/residents", data={
        "action":"edit","rid":str(editable),"year":"3","repeat_year":"0","status":"active"
    }, follow_redirects=True)
    assert year_change.status_code == 200
    assert "Tout changement d’année doit passer par le processus officiel".encode() in year_change.data
    with rotation_app.db() as conn:
        row = conn.execute("SELECT year,status FROM residents WHERE id=?", (editable,)).fetchone()
        assert tuple(row) == (2,"inactive")

    bypass_response = client.post("/residents", data={
        "action":"edit","rid":str(bypass),"year":"4","repeat_year":"0","status":"graduated"
    }, follow_redirects=True)
    assert bypass_response.status_code == 200
    with rotation_app.db() as conn:
        assert conn.execute("SELECT status FROM residents WHERE id=?", (bypass,)).fetchone()[0] == "active"

    restore_response = client.post("/residents", data={
        "action":"edit","rid":str(graduated),"year":"4","repeat_year":"0","status":"active"
    }, follow_redirects=True)
    assert restore_response.status_code == 200
    assert "Les résidents diplômés sont archivés".encode() in restore_response.data
    with rotation_app.db() as conn:
        assert conn.execute("SELECT status FROM residents WHERE id=?", (graduated,)).fetchone()[0] == "graduated"
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE action='resident.updated'").fetchone()[0] == 1

def test_first_year_evaluation_does_not_record_decision_for_resident_in_later_year(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,2,'active')", ("LaterYear", "Resident"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='LaterYear'").fetchone()[0]
        conn.execute(
            "INSERT INTO exam_records(resident_id,study_year,module,theory,practical) VALUES(?,1,?,?,?)",
            (rid,"Module A",12,12),
        )
        conn.commit()

    response = client.post("/exams", data={
        "action":"evaluate_first_year","resident":str(rid),"study_year":"1",
        "all_modules_confirmed":"yes"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "Seuls les résidents actuellement en première année".encode() in response.data
    with rotation_app.db() as conn:
        assert conn.execute("SELECT year FROM residents WHERE id=?", (rid,)).fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM decisions WHERE details LIKE ?", (f"%LaterYear Resident — first-year exams%",)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE action='exam.first_year_evaluated'").fetchone()[0] == 0

def test_startup_fills_missing_periods_in_partial_legacy_academic_year(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    legacy = sqlite3.connect(rotation_app.DB)
    legacy.execute(
        "CREATE TABLE periods(id INTEGER PRIMARY KEY,year_label TEXT NOT NULL,name TEXT NOT NULL,UNIQUE(year_label,name))"
    )
    legacy.execute("INSERT INTO periods(year_label,name) VALUES(?,?)", ("2026-2027","01 Fév - 30 Avr"))
    legacy.execute("CREATE TABLE settings(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
    legacy.execute("INSERT INTO settings(key,value) VALUES('year','2026-2027')")
    legacy.commit()
    legacy.close()

    assert client.get("/login").status_code == 200
    expected = {"Période 1","Période 2","Période 3","Période 4"}
    with rotation_app.db() as conn:
        names = {row[0] for row in conn.execute("SELECT name FROM periods WHERE year_label='2026-2027'")}
        assert names == expected
        assert conn.execute("SELECT COUNT(*) FROM periods WHERE year_label='2026-2027'").fetchone()[0] == 4

    monkeypatch.setattr(rotation_app.app, "_ready", False, raising=False)
    assert client.get("/login").status_code == 200
    with rotation_app.db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM periods WHERE year_label='2026-2027'").fetchone()[0] == 4

def test_import_rejects_fractional_study_year_instead_of_truncating(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    source = b"surname,firstname,year,phone\nFractional,Resident,2.5,0550000000\n"
    response = client.post(
        "/import",
        data={"file":(io.BytesIO(source),"fractional-year.csv")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "L’année doit être 1, 2, 3 ou 4".encode() in response.data
    with rotation_app.db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM residents WHERE surname='Fractional'").fetchone()[0] == 0

def test_deactivated_account_loses_existing_session_immediately(tmp_path, monkeypatch):
    admin = setup_client(tmp_path, monkeypatch)
    login(admin)
    username = "revoked-session"
    password = "strong-revoked-password-2026"
    admin.post("/users", data={"username":username,"password":password,"role":"user"}, follow_redirects=True)

    user_client = rotation_app.app.test_client()
    signed_in = user_client.post(
        "/login", data={"username":username,"password":password}, follow_redirects=True
    )
    assert signed_in.status_code == 200
    assert user_client.get("/").status_code == 200

    with rotation_app.db() as conn:
        uid = conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()[0]
    admin.post("/users", data={"action":"deactivate","user_id":str(uid)}, follow_redirects=True)

    revoked = user_client.get("/")
    assert revoked.status_code == 302
    assert "/login" in revoked.headers["Location"]
    with user_client.session_transaction() as session:
        assert "user" not in session

def test_standard_user_cannot_create_rotation_assignments(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    client.post("/users", data={
        "username":"assignment-operator",
        "password":"assignment-operator-password-2026",
        "role":"user",
    }, follow_redirects=True)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,2)", ("NoAssign", "Resident"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='NoAssign'").fetchone()[0]
        tid = conn.execute("SELECT id FROM terrains WHERE name='Réanimation chirurgicale'").fetchone()[0]
        period = conn.execute("SELECT id,year_label FROM periods ORDER BY id LIMIT 1").fetchone()
        conn.execute(
            "INSERT INTO capacities(year_label,terrain_id,period_id,places) VALUES(?,?,?,1)",
            (period["year_label"],tid,period["id"]),
        )
        conn.commit()
    with client.session_transaction() as session:
        session["user"]="assignment-operator"
        session["role"]="user"
        session["lang"]="en"

    read_only = client.get("/assign")
    assert read_only.status_code == 200
    assert b"Only Super Admins can create assignments." in read_only.data
    assert b'id="assignment-form"' not in read_only.data

    response = client.post("/assign", data={
        "resident":str(rid),"terrain":str(tid),"period":str(period["id"])
    })
    assert response.status_code == 403
    with rotation_app.db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM assignments WHERE resident_id=?", (rid,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE action='assignment.created'").fetchone()[0] == 0

def test_history_rejects_invalid_year_period_and_duplicate_records(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,1)", ("History", "Resident"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='History'").fetchone()[0]
        tid = conn.execute("SELECT id FROM terrains WHERE name='Réanimation chirurgicale'").fetchone()[0]
        conn.commit()

    invalid_year = client.post("/history", data={
        "resident":str(rid),"terrain":str(tid),"year_label":"2025-2027",
        "period":"01 Fév - 30 Avr","date_done":"2026-03-01"
    }, follow_redirects=True)
    assert invalid_year.status_code == 200
    assert "L’année de post-graduation doit suivre le format".encode() in invalid_year.data

    invalid_period = client.post("/history", data={
        "resident":str(rid),"terrain":str(tid),"year_label":"2025-2026",
        "period":"invented period","date_done":"2026-03-01"
    }, follow_redirects=True)
    assert invalid_period.status_code == 200
    assert "Choisissez l’une des quatre périodes officielles".encode() in invalid_period.data

    future_date = client.post("/history", data={
        "resident":str(rid),"terrain":str(tid),"year_label":"2098-2099",
        "period":"01 Fév - 30 Avr","date_done":"2098-03-01"
    }, follow_redirects=True)
    assert future_date.status_code == 200
    assert "Une date de stage historique ne peut pas être dans le futur".encode() in future_date.data

    payload = {
        "resident":str(rid),"terrain":str(tid),"year_label":"2025-2026",
        "period":"01 Fév - 30 Avr","date_done":"2026-03-01"
    }
    first = client.post("/history", data=payload, follow_redirects=True)
    assert first.status_code == 200
    second = client.post("/history", data=payload, follow_redirects=True)
    assert second.status_code == 200
    assert "Ce stage historique existe déjà".encode() in second.data
    with rotation_app.db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM history WHERE resident_id=? AND terrain_id=?", (rid,tid)).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE action='history.created'").fetchone()[0] == 1

def test_inactive_resident_cannot_receive_promotion_votes(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    client.post("/users", data={
        "username":"benhocine",
        "password":"official-admin-password-2026",
        "role":"super_admin",
    }, follow_redirects=True)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,2,'inactive')", ("Inactive", "Promotion"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Inactive'").fetchone()[0]
        conn.commit()

    with client.session_transaction() as session:
        session["user"]="benhocine"
        session["role"]="super_admin"
    first = client.post("/exams", data={
        "action":"approve_advance","resident":str(rid),"study_year":"2",
        "outcome":"approve","reason":"Should not count"
    }, follow_redirects=True)
    assert first.status_code == 200
    assert "Un résident inactif ne peut pas être promu".encode() in first.data
    with rotation_app.db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM promotion_votes WHERE resident_id=?", (rid,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE action='promotion.vote_recorded'").fetchone()[0] == 0

def test_future_confirmed_rotations_do_not_count_as_completed_for_repeat_eligibility(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    client.get("/lang/ar", headers={"Referer": "http://localhost/"})
    login(client)
    with rotation_app.db() as conn:
        rid = conn.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES(?,?,4) RETURNING id",
            ("Future", "Rotations"),
        ).fetchone()[0]
        current_period = conn.execute("SELECT * FROM periods ORDER BY id LIMIT 1").fetchone()
        target = conn.execute(
            "SELECT id FROM terrains WHERE name='Réanimation chirurgicale'"
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO capacities(year_label,terrain_id,period_id,places) VALUES(?,?,?,2)",
            (current_period["year_label"],target,current_period["id"]),
        )
        conn.execute(
            "INSERT INTO history(resident_id,terrain_id,year_label,period,date_done) VALUES(?,?,?,?,?)",
            (rid,target,"2025-2026","01 Fév - 30 Avr","2026-04-30"),
        )
        future_terrains = conn.execute(
            "SELECT id FROM terrains WHERE active=1 AND kind IN ('mandatory','basic') AND id<>?",
            (target,),
        ).fetchall()
        for index, terrain_row in enumerate(future_terrains):
            start_year = 2099 + index
            future_period_id = conn.execute(
                "INSERT INTO periods(year_label,name) VALUES(?,?) RETURNING id",
                (f"{start_year}-{start_year+1}","01 Fév - 30 Avr"),
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO assignments(resident_id,terrain_id,period_id,status) VALUES(?,?,?,'confirmed')",
                (rid,terrain_row["id"],future_period_id),
            )
        conn.commit()

    with rotation_app.app.test_request_context("/"):
        with rotation_app.db() as conn:
            allowed, message, status = rotation_app.check(
                conn,rid,target,current_period["id"],current_period["year_label"]
            )
    assert allowed is False
    assert "Stage déjà effectué" in message

def test_capacity_rejects_negative_and_cross_academic_year_periods(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        terrain_id = conn.execute(
            "SELECT id FROM terrains WHERE active=1 ORDER BY id LIMIT 1"
        ).fetchone()[0]
        current = conn.execute("SELECT id,year_label FROM periods ORDER BY id LIMIT 1").fetchone()
        other_period_id = conn.execute(
            "INSERT INTO periods(year_label,name) VALUES(?,?) RETURNING id",
            ("2099-2100","01 Fév - 30 Avr"),
        ).fetchone()[0]
        conn.commit()

    negative = client.post("/capacities", data={
        "terrain":str(terrain_id),"period":str(current["id"]),"places":"-1"
    }, follow_redirects=True)
    assert negative.status_code == 200
    assert b"Invalid capacity input" in negative.data

    wrong_year = client.post("/capacities", data={
        "terrain":str(terrain_id),"period":str(other_period_id),"places":"3"
    }, follow_redirects=True)
    assert wrong_year.status_code == 200
    assert b"Invalid capacity input" in wrong_year.data

    with rotation_app.db() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM capacities WHERE terrain_id=? AND period_id=?",
            (terrain_id,other_period_id),
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM capacities WHERE terrain_id=? AND period_id=? AND places<0",
            (terrain_id,current["id"]),
        ).fetchone()[0] == 0

def test_import_confirmation_rechecks_duplicates_and_imports_nothing_on_stale_preview(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    source = (
        b"surname,firstname,year,phone\n"
        b"Fresh,Resident,2,0550000001\n"
        b"Race,Condition,3,0550000002\n"
    )
    preview = client.post("/import", data={
        "file": (io.BytesIO(source), "residents.csv")
    }, content_type="multipart/form-data", follow_redirects=True)
    assert preview.status_code == 200
    match = re.search(rb'name="preview_id" value="(\d+)"', preview.data)
    assert match

    # Simulate another administrator adding a resident after the preview was made.
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES(?,?,3)",
            ("Race", "Condition"),
        )
        conn.commit()

    confirmed = client.post("/import", data={
        "action":"confirm", "preview_id":match.group(1).decode()
    }, follow_redirects=True)
    assert confirmed.status_code == 200
    assert "Rien n’a été importé".encode() in confirmed.data
    with rotation_app.db() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM residents WHERE surname='Fresh' AND firstname='Resident'"
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM residents WHERE surname='Race' AND firstname='Condition' AND year=3"
        ).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE action='residents.imported'").fetchone()[0] == 0

def test_repeat_of_core_terrain_is_blocked_across_academic_years(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        rid = conn.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES(?,?,4) RETURNING id",
            ("CrossYear", "Repeat"),
        ).fetchone()[0]
        target = conn.execute(
            "SELECT id FROM terrains WHERE active=1 AND kind IN ('mandatory','basic') ORDER BY id LIMIT 1"
        ).fetchone()[0]
        current_year = conn.execute("SELECT value FROM settings WHERE key='year'").fetchone()[0]
        current_period = conn.execute(
            "SELECT id,year_label FROM periods WHERE year_label=? ORDER BY id LIMIT 1",
            (current_year,),
        ).fetchone()
        conn.execute(
            "INSERT INTO capacities(year_label,terrain_id,period_id,places) VALUES(?,?,?,1)",
            (current_year,target,current_period["id"]),
        )
        previous_period = conn.execute(
            "INSERT INTO periods(year_label,name) VALUES(?,?) RETURNING id",
            ("2024-2025","01 Fév - 30 Avr"),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO assignments(resident_id,terrain_id,period_id,status) VALUES(?,?,?,'confirmed')",
            (rid,target,previous_period),
        )
        conn.commit()

    with rotation_app.app.test_request_context("/"):
        with rotation_app.db() as conn:
            allowed, message, status = rotation_app.check(
                conn,rid,target,current_period["id"],current_year
            )
    assert allowed is False
    assert status is None

def test_future_dated_history_does_not_unlock_core_terrain_repeats(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        rid = conn.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES(?,?,4) RETURNING id",
            ("FutureHistory", "Resident"),
        ).fetchone()[0]
        current_period = conn.execute("SELECT * FROM periods ORDER BY id LIMIT 1").fetchone()
        terrains = conn.execute(
            "SELECT id FROM terrains WHERE active=1 AND kind IN ('mandatory','basic')"
        ).fetchall()
        target = terrains[0]["id"]
        conn.execute(
            "INSERT INTO capacities(year_label,terrain_id,period_id,places) VALUES(?,?,?,1)",
            (current_period["year_label"],target,current_period["id"]),
        )
        for terrain in terrains:
            conn.execute(
                "INSERT INTO history(resident_id,terrain_id,year_label,period,date_done) VALUES(?,?,?,?,?)",
                (rid,terrain["id"],"2098-2099","01 Fév - 30 Avr","2098-03-01"),
            )
        conn.commit()

    with rotation_app.app.test_request_context("/"):
        with rotation_app.db() as conn:
            allowed, message, status = rotation_app.check(
                conn,rid,target,current_period["id"],current_period["year_label"]
            )
    assert allowed is False
    assert status is None

def test_undated_future_history_does_not_unlock_core_terrain_repeats(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        rid = conn.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES(?,?,4) RETURNING id",
            ("UndatedFuture", "History"),
        ).fetchone()[0]
        current_period = conn.execute("SELECT * FROM periods ORDER BY id LIMIT 1").fetchone()
        terrains = conn.execute(
            "SELECT id FROM terrains WHERE active=1 AND kind IN ('mandatory','basic')"
        ).fetchall()
        target = terrains[0]["id"]
        conn.execute(
            "INSERT INTO capacities(year_label,terrain_id,period_id,places) VALUES(?,?,?,1)",
            (current_period["year_label"], target, current_period["id"]),
        )
        for terrain in terrains:
            conn.execute(
                "INSERT INTO history(resident_id,terrain_id,year_label,period,date_done) VALUES(?,?,?,?, '')",
                (rid, terrain["id"], "2098-2099", "01 Fév - 30 Avr"),
            )
        conn.commit()

    with rotation_app.app.test_request_context("/"):
        with rotation_app.db() as conn:
            allowed, message, status = rotation_app.check(
                conn, rid, target, current_period["id"], current_period["year_label"]
            )
    assert allowed is False
    assert status is None
    assert "repetition" not in message.lower() or "completed" not in message.lower()


def test_exam_recording_rejects_future_year_and_graduated_resident(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        future_id = conn.execute(
            "INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,2,'active') RETURNING id",
            ("FutureYear", "Exam"),
        ).fetchone()[0]
        graduated_id = conn.execute(
            "INSERT INTO residents(surname,firstname,year,status,dems_status) VALUES(?, ?,4,'graduated','success') RETURNING id",
            ("Graduated", "Exam"),
        ).fetchone()[0]
        conn.commit()

    future = client.post("/exams", data={
        "action":"record","resident":str(future_id),"study_year":"3",
        "module":"Future Module","theory":"15","practical":"15"
    }, follow_redirects=True)
    assert future.status_code == 200
    assert "Impossible d’enregistrer des notes pour une année future".encode() in future.data

    graduated = client.post("/exams", data={
        "action":"record","resident":str(graduated_id),"study_year":"4",
        "module":"Late Module","theory":"15","practical":"15"
    }, follow_redirects=True)
    assert graduated.status_code == 200
    assert "Impossible d’enregistrer des notes pour une année future".encode() in graduated.data

    with rotation_app.db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM exam_records WHERE resident_id IN (?,?)", (future_id,graduated_id)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE action IN ('exam.recorded','exam.updated')").fetchone()[0] == 0

def test_terrain_classification_cannot_change_after_rotation_records_exist(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        resident_id = conn.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES(?,?,2) RETURNING id",
            ("Terrain", "Audit"),
        ).fetchone()[0]
        terrain = conn.execute(
            "SELECT id,kind,mandatory_year,name FROM terrains WHERE active=1 ORDER BY id LIMIT 1"
        ).fetchone()
        conn.execute(
            "INSERT INTO history(resident_id,terrain_id,year_label,period,date_done) VALUES(?,?,?,?,?)",
            (resident_id,terrain["id"],"2025-2026","01 Fév - 30 Avr","2026-04-30"),
        )
        conn.commit()

    response = client.post("/terrains", data={
        "action":"edit","tid":str(terrain["id"]),"name":terrain["name"],
        "kind":"optional" if terrain["kind"]!="optional" else "mandatory",
        "mandatory_year":str(terrain["mandatory_year"]),
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Terrain classification/year cannot be changed after rotation history or assignments exist" in response.data
    with rotation_app.db() as conn:
        unchanged = conn.execute("SELECT kind,mandatory_year FROM terrains WHERE id=?", (terrain["id"],)).fetchone()
        assert unchanged["kind"] == terrain["kind"]
        assert unchanged["mandatory_year"] == terrain["mandatory_year"]
        assert conn.execute("SELECT COUNT(*) FROM history WHERE resident_id=? AND terrain_id=?", (resident_id,terrain["id"])).fetchone()[0] == 1

def test_profile_rejects_invalid_identity_and_preserves_photo_when_omitted(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        rid = conn.execute(
            "INSERT INTO residents(surname,firstname,year,birth_place,birth_date,photo_path,phone) VALUES(?,?,?,?,?,?,?) RETURNING id",
            ("Original","Resident",2,"Tizi Ouzou","1990-01-01","/photos/resident_1.png","0550000000"),
        ).fetchone()[0]
        conn.commit()
    client.get(f"/profile/{rid}")

    invalid = client.post(f"/profile/{rid}", data={
        "surname":"   ","firstname":"Resident","birth_date":"2099-01-01"
    }, follow_redirects=True)
    assert invalid.status_code == 200
    assert "Le nom et le prénom sont obligatoires".encode() in invalid.data
    with rotation_app.db() as conn:
        row = conn.execute("SELECT surname,photo_path FROM residents WHERE id=?",(rid,)).fetchone()
        assert row["surname"] == "Original"
        assert row["photo_path"] == "/photos/resident_1.png"

    valid = client.post(f"/profile/{rid}", data={
        "surname":"Updated","firstname":"Resident","birth_place":"Tizi Ouzou",
        "birth_date":"1990-01-01","phone":"0550000000"
    }, follow_redirects=True)
    assert valid.status_code == 200
    with rotation_app.db() as conn:
        row = conn.execute("SELECT surname,photo_path FROM residents WHERE id=?",(rid,)).fetchone()
        assert row["surname"] == "Updated"
        assert row["photo_path"] == "/photos/resident_1.png"

def test_resident_creation_validates_repeat_flag_lengths_and_duplicate_names(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    invalid_flag = client.post("/residents", data={
        "surname":"Valid","firstname":"Flag","year":"1","repeat_year":"yes"
    }, follow_redirects=True)
    assert invalid_flag.status_code == 200
    assert "le champ redoublement doit valoir 0 ou 1".encode() in invalid_flag.data

    long_phone = client.post("/residents", data={
        "surname":"Valid","firstname":"Phone","year":"1","phone":"x"*41
    }, follow_redirects=True)
    assert long_phone.status_code == 200
    assert "Le téléphone doit contenir au maximum 40 caractères".encode() in long_phone.data

    payload = {"surname":"Test","firstname":"Resident","year":"2","phone":"0550000000","repeat_year":"0"}
    first = client.post("/residents", data=payload, follow_redirects=True)
    assert first.status_code == 200
    second = client.post("/residents", data={**payload,"surname":" test "}, follow_redirects=True)
    assert second.status_code == 200
    assert "Un résident portant le même nom et la même année d’étude existe déjà".encode() in second.data
    with rotation_app.db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM residents WHERE lower(surname)='test' AND lower(firstname)='resident' AND year=2").fetchone()[0] == 1

def test_objectives_reject_invalid_year_inactive_terrain_and_duplicates(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        terrain = conn.execute("SELECT id FROM terrains WHERE active=1 ORDER BY id LIMIT 1").fetchone()[0]
        conn.execute("INSERT INTO terrains(name,kind,active) VALUES('Inactive objective terrain','basic',0)")
        inactive = conn.execute("SELECT id FROM terrains WHERE name='Inactive objective terrain'").fetchone()[0]
        conn.commit()

    invalid_year = client.post("/objectives", data={
        "terrain":str(terrain),"study_year":"5","objective":"Objective"
    }, follow_redirects=True)
    assert invalid_year.status_code == 200
    assert b"Objective study year must be 1, 2, 3 or 4" in invalid_year.data

    inactive_terrain = client.post("/objectives", data={
        "terrain":str(inactive),"study_year":"1","objective":"Objective"
    }, follow_redirects=True)
    assert inactive_terrain.status_code == 200
    assert b"Choose an active terrain" in inactive_terrain.data

    payload = {"terrain":str(terrain),"study_year":"1","objective":"Clinical skills"}
    first = client.post("/objectives", data=payload, follow_redirects=True)
    assert first.status_code == 200
    second = client.post("/objectives", data=payload, follow_redirects=True)
    assert second.status_code == 200
    assert b"This objective already exists" in second.data
    with rotation_app.db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM objectives WHERE terrain_id=? AND study_year=1 AND objective='Clinical skills'",(terrain,)).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM objectives WHERE terrain_id=? AND study_year=5",(terrain,)).fetchone()[0] == 0

def test_documented_history_import_requires_preview_and_rejects_future_dates(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,3)", ("HistoryImport", "Resident"))
        conn.commit()

    valid_csv = (
        "resident,terrain,year_label,period,date_done\n"
        "HistoryImport Resident,Réanimation chirurgicale,2025-2026,01 Fév - 30 Avr,2026-04-30\n"
    ).encode("utf-8")
    preview = client.post(
        "/import-history",
        data={"file":(io.BytesIO(valid_csv),"history.csv")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert preview.status_code == 200
    assert b"HistoryImport Resident" in preview.data
    assert "Confirmer l’importation".encode() in preview.data
    with rotation_app.db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM history").fetchone()[0] == 0
    match = re.search(rb'name="preview_id" value="(\d+)"', preview.data)
    assert match
    confirmed = client.post("/import-history", data={
        "action":"confirm","preview_id":match.group(1).decode()
    }, follow_redirects=True)
    assert confirmed.status_code == 200
    with rotation_app.db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM history h JOIN residents r ON r.id=h.resident_id WHERE r.surname='HistoryImport'").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE action='history.imported'").fetchone()[0] == 1

    future_csv = (
        "resident,terrain,year_label,period,date_done\n"
        "HistoryImport Resident,Réanimation polyvalente,2026-2027,01 Fév - 30 Avr,2099-03-01\n"
    ).encode("utf-8")
    future_preview = client.post(
        "/import-history",
        data={"file":(io.BytesIO(future_csv),"future-history.csv")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert future_preview.status_code == 200
    assert "Une date de stage historique ne peut pas être dans le futur".encode() in future_preview.data
    assert b"disabled" in future_preview.data
    with rotation_app.db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM history h JOIN residents r ON r.id=h.resident_id WHERE r.surname='HistoryImport'").fetchone()[0] == 1

def test_exam_route_rejects_malformed_ids_and_scores_without_server_error(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        rid = conn.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES(?,?,1) RETURNING id",
            ("Malformed", "ExamInput"),
        ).fetchone()[0]
        conn.commit()

    bad_year = client.post("/exams", data={
        "action":"record","resident":str(rid),"study_year":"not-a-year",
        "module":"Module A","theory":"12","practical":"13",
    }, follow_redirects=True)
    assert bad_year.status_code == 200
    assert "Choisissez un résident et une année d’étude valides".encode() in bad_year.data

    bad_score = client.post("/exams", data={
        "action":"record","resident":str(rid),"study_year":"1",
        "module":"Module A","theory":"not-a-number","practical":"13",
    }, follow_redirects=True)
    assert bad_score.status_code == 200
    assert b"numeric marks from 0 to 20 are required" in bad_score.data

    with rotation_app.db() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM exam_records WHERE resident_id=?", (rid,)
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM audit WHERE action IN ('exam.recorded','exam.updated')"
        ).fetchone()[0] == 0



def test_dems_rejects_future_exam_date_without_vote_or_audit(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    for username in ("benhocine", "drdris"):
        client.post("/users", data={
            "username": username,
            "password": "strong-test-password-2026",
            "role": "super_admin",
        }, follow_redirects=True)
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES(?,?,4)",
            ("FutureDEMS", "Resident"),
        )
        rid = conn.execute(
            "SELECT id FROM residents WHERE surname='FutureDEMS'"
        ).fetchone()[0]
        conn.commit()

    future_date = (rotation_app.date.today() + timedelta(days=1)).isoformat()
    with client.session_transaction() as sess:
        sess["user"] = "benhocine"
        sess["role"] = "super_admin"
    response = client.post("/dems", data={
        "resident": str(rid),
        "success_date": future_date,
        "outcome": "approve",
        "reason": "Should not be accepted",
    }, follow_redirects=True)

    assert response.status_code == 200
    assert "La date de l’examen DEMS ne peut pas être dans le futur".encode() in response.data
    with rotation_app.db() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM dems_votes WHERE resident_id=?", (rid,)
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM dems_archive WHERE resident_id=?", (rid,)
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM audit WHERE action='dems.vote_recorded'"
        ).fetchone()[0] == 0


def test_admin_routes_handle_malformed_record_ids_without_server_error(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)

    decision_response = client.post("/decisions", data={
        "aid": "not-an-id",
        "outcome": "reject",
        "reason": "Malformed request",
    }, follow_redirects=True)
    assert decision_response.status_code == 200

    user_response = client.post("/users", data={
        "action": "deactivate",
        "user_id": "not-a-user-id",
    }, follow_redirects=True)
    assert user_response.status_code == 200

    with rotation_app.db() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM decisions WHERE reason='Malformed request'"
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM audit WHERE action IN ('assignment.override_approved','assignment.override_rejected','user.deactivated','user.activated')"
        ).fetchone()[0] == 0


def test_profile_photo_picker_accepts_supported_extensions_without_rejecting_generic_android_mime(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        rid = conn.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES(?,?,1) RETURNING id",
            ("Photo", "Picker"),
        ).fetchone()[0]
        conn.commit()
    response = client.get(f"/profile/{rid}")
    assert response.status_code == 200
    assert b'accept=".png,.jpg,.jpeg,.webp,image/png,image/jpeg,image/webp"' in response.data
    html = response.get_data(as_text=True)
    assert "!['png','jpg','jpeg','webp'].includes(ext)" in html
    assert "file.type&&!allowed.includes(file.type)" not in html
    assert "reader.onerror=function()" in html


def test_resident_profile_photo_frame_is_large_and_responsive(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        rid = conn.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES(?,?,2) RETURNING id",
            ("Avatar", "Sizing"),
        ).fetchone()[0]
        conn.commit()

    response = client.get(f"/profile/{rid}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    # Desktop/tablet: scale fluidly up to 240 px; phones stack the header and use a 240 px photo.
    assert ".rt-avatar-wrap{flex:0 0 auto;width:clamp(220px,30vw,280px)}" in html
    assert ".rt-profile-avatar{display:block;width:100%;height:clamp(220px,30vw,280px);object-fit:cover" in html
    assert ".rt-profile-head{align-items:stretch;flex-direction:column;gap:14px}" in html
    assert ".rt-avatar-wrap{width:min(260px,100%);flex-basis:auto;align-self:center}" in html
    assert ".rt-profile-avatar{height:260px;border-radius:20px}" in html



def test_windows_launcher_keeps_user_data_and_secret_outside_install_folder(tmp_path, monkeypatch):
    import windows_launcher as desktop_launcher

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "LocalAppData"))
    data_dir = desktop_launcher._prepare_user_data()
    secret_path = data_dir / ".rotation_secret"
    secret_before = secret_path.read_text(encoding="ascii")

    assert data_dir == tmp_path / "LocalAppData" / "ResiManage" / "data"
    assert secret_path.is_file()
    assert len(secret_before) >= 32
    assert desktop_launcher._prepare_user_data() == data_dir
    assert secret_path.read_text(encoding="ascii") == secret_before


def test_windows_packaging_bundles_static_assets_and_uses_separate_user_data():
    project_root = Path(__file__).resolve().parents[1]
    workflow = (project_root / ".github/workflows/build-resimanage-windows.yml").read_text(
        encoding="utf-8"
    )
    launcher = (project_root / "windows_launcher.py").read_text(encoding="utf-8")

    assert '--add-data "static;static"' in workflow
    assert 'root / "ResiManage" / "data"' in launcher
    assert 'resimanage.DB = str(data_dir / "rotation.db")' in launcher
    assert 'make_server(host, port, resimanage.app, threaded=True, ssl_context=ssl_context)' in launcher
    assert 'RESIMANAGE_BIND' in launcher and 'RESIMANAGE_TLS_CERT' in launcher


def test_internal_favicon_declares_the_jpeg_mime_type(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    response = client.get("/")
    assert response.status_code == 200
    assert b'type="image/jpeg" href="/static/resimanage-3d-icon.jpg"' in response.data
    assert b'type="image/svg+xml" href="/static/resimanage-3d-icon.jpg"' not in response.data


def test_registration_password_fields_have_visibility_toggles(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    response = client.get("/register")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'id="register-password"' in html
    assert 'id="register-confirm-password"' in html
    assert html.count('class="password-toggle"') >= 2
    assert "Hide password" in html


def test_admin_password_fields_have_visibility_toggles(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    settings_response = client.get("/settings")
    users_response = client.get("/users")
    assert settings_response.status_code == 200
    assert users_response.status_code == 200
    assert 'id="settings-new-password"' in settings_response.get_data(as_text=True)
    assert 'id="new-user-password"' in users_response.get_data(as_text=True)
    assert 'class="password-toggle"' in settings_response.get_data(as_text=True)
    assert 'class="password-toggle"' in users_response.get_data(as_text=True)


def test_login_accepts_registered_email_as_identifier(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute(
            "UPDATE users SET email=?,email_verified=1 WHERE username='admin'",
            ("admin.login@example.com",),
        )
    client.get("/logout")
    response = client.post(
        "/login",
        data={
            "username": "ADMIN.LOGIN@example.com",
            "password": "test-strong-password-2026",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Résidents".encode() in response.data


def test_objective_completion_is_toggleable_audited_and_color_coded(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        terrain_id = conn.execute(
            "SELECT id FROM terrains WHERE name='Réanimation chirurgicale'"
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO objectives(terrain_id,study_year,objective) VALUES(?,?,?)",
            (terrain_id, 2, "Manage airway"),
        )
        objective_id = conn.execute(
            "SELECT id FROM objectives WHERE objective='Manage airway'"
        ).fetchone()[0]

    response = client.post(
        "/objectives",
        data={"action": "toggle", "objective_id": str(objective_id), "completed": "1"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "#fee2e2" in html
    assert "Effectué" in html
    with rotation_app.db() as conn:
        assert conn.execute(
            "SELECT completed FROM objectives WHERE id=?", (objective_id,)
        ).fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM audit WHERE action='objective.completed'"
        ).fetchone()[0] == 1

    client.post(
        "/objectives",
        data={"action": "toggle", "objective_id": str(objective_id), "completed": "0"},
        follow_redirects=True,
    )
    with rotation_app.db() as conn:
        assert conn.execute(
            "SELECT completed FROM objectives WHERE id=?", (objective_id,)
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM audit WHERE action='objective.reopened'"
        ).fetchone()[0] == 1


def test_resident_profile_displays_objective_completion_status(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES(?,?,?)",
            ("ObjectiveColor", "Resident", 2),
        )
        rid = conn.execute(
            "SELECT id FROM residents WHERE surname='ObjectiveColor'"
        ).fetchone()[0]
        terrain_id = conn.execute(
            "SELECT id FROM terrains WHERE name='Réanimation chirurgicale'"
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO objectives(terrain_id,study_year,objective,completed) VALUES(?,?,?,?)",
            (terrain_id, 2, "Airway objective", 1),
        )
    response = client.get(f"/profile/{rid}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "#fee2e2" in html
    assert "Airway objective" in html
    assert "Effectué" in html


def test_future_confirmed_rotation_is_not_shown_as_completed_in_profile(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES(?,?,?)",
            ("FutureProfile", "Resident", 3),
        )
        rid = conn.execute(
            "SELECT id FROM residents WHERE surname='FutureProfile'"
        ).fetchone()[0]
        terrain_id = conn.execute(
            "SELECT id FROM terrains WHERE name='Réanimation chirurgicale'"
        ).fetchone()[0]
        period = conn.execute(
            "SELECT id,year_label,name FROM periods WHERE name='Période 4' ORDER BY year_label DESC LIMIT 1"
        ).fetchone()
        conn.execute(
            "INSERT INTO assignments(resident_id,terrain_id,period_id,status) VALUES(?,?,?,'confirmed')",
            (rid, terrain_id, period["id"]),
        )
    response = client.get(f"/profile/{rid}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'class="good">À faire' in html


def test_windows_launcher_migrates_existing_database_and_photos_without_deleting_source(tmp_path):
    import windows_launcher as desktop_launcher

    legacy_root = tmp_path / "legacy-install"
    data_dir = tmp_path / "user-data"
    legacy_root.mkdir()
    data_dir.mkdir()
    legacy_db = legacy_root / "rotation.db"
    with sqlite3.connect(legacy_db) as conn:
        conn.execute("CREATE TABLE preserved_records(value TEXT)")
        conn.execute("INSERT INTO preserved_records(value) VALUES('keep-me')")
    legacy_photos = legacy_root / "resident_photos"
    legacy_photos.mkdir()
    (legacy_photos / "resident_1.jpg").write_bytes(b"legacy-photo")
    (legacy_photos / "resident_2.jpg").write_bytes(b"new-photo")
    target_photos = data_dir / "resident_photos"
    target_photos.mkdir()
    (target_photos / "resident_1.jpg").write_bytes(b"keep-newer-photo")

    desktop_launcher._migrate_legacy_data(data_dir, legacy_root)

    with sqlite3.connect(data_dir / "rotation.db") as conn:
        assert conn.execute("SELECT value FROM preserved_records").fetchone()[0] == "keep-me"
    assert (target_photos / "resident_1.jpg").read_bytes() == b"keep-newer-photo"
    assert (target_photos / "resident_2.jpg").read_bytes() == b"new-photo"
    assert legacy_db.is_file()
    assert (legacy_photos / "resident_1.jpg").is_file()


def test_objective_completion_column_migrates_legacy_database(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    with sqlite3.connect(rotation_app.DB) as conn:
        conn.execute(
            "CREATE TABLE objectives(id INTEGER PRIMARY KEY,terrain_id INTEGER NOT NULL,study_year INTEGER NOT NULL,objective TEXT NOT NULL)"
        )
    login(client)
    with rotation_app.db() as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(objectives)")}
        assert "completed" in columns
        assert conn.execute(
            "SELECT dflt_value FROM pragma_table_info('objectives') WHERE name='completed'"
        ).fetchone()[0] == "0"


def test_selected_language_persists_after_login(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    client.get("/lang/fr", headers={"Referer": "http://localhost/login"})
    with client.session_transaction() as session:
        assert session.get("lang") == "fr"

    response = login(client)
    assert response.status_code == 200
    assert "Accueil".encode() in response.data
    assert "Résidents".encode() in response.data
    with client.session_transaction() as session:
        assert session.get("lang") == "fr"


def test_language_selectors_show_algerian_french_and_english_flags(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login_page = client.get("/login")
    assert "🇩🇿 العربية".encode() in login_page.data
    assert "🇫🇷 Français".encode() in login_page.data
    assert "🇬🇧 English".encode() in login_page.data

    login(client)
    home_page = client.get("/")
    assert "🇩🇿".encode() in home_page.data
    assert "🇫🇷".encode() in home_page.data
    assert "🇬🇧".encode() in home_page.data


def test_android_python_bundle_includes_static_brand_assets():
    project_root = Path(__file__).resolve().parents[1]
    gradle = (project_root / "android/app/build.gradle").read_text(encoding="utf-8")
    brand_image = project_root / "static/resimanage-3d-icon.jpg"
    assert "copyRotationStaticAssets" in gradle
    assert 'into(layout.projectDirectory.dir("src/main/python/static"))' in gradle
    assert brand_image.is_file()


def test_android_launcher_icon_is_bundled_from_current_brand_artwork():
    project_root = Path(__file__).resolve().parents[1]
    manifest = (project_root / "android/app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
    gradle = (project_root / "android/app/build.gradle").read_text(encoding="utf-8")
    brand_image = project_root / "static/resimanage-3d-icon.jpg"
    assert 'android:icon="@drawable/resimanage_3d_launcher"' in manifest
    assert 'android:roundIcon="@drawable/resimanage_3d_launcher"' in manifest
    assert 'copyRotationLauncherIcon' in gradle
    assert 'rename { "resimanage_3d_launcher.jpg" }' in gradle
    assert brand_image.is_file()

def test_android_package_version_identifies_resimanage_2():
    gradle = (
        Path(__file__).resolve().parents[1] / "android/app/build.gradle"
    ).read_text(encoding="utf-8")
    assert "versionCode 2" in gradle
    assert 'versionName "2.0.0"' in gradle


def test_android_gradle_project_uses_current_resimanage_name():
    settings = (
        Path(__file__).resolve().parents[1] / "android/settings.gradle"
    ).read_text(encoding="utf-8")
    assert 'rootProject.name = "ResiManage"' in settings
    assert 'rootProject.name = "RotationApp"' not in settings


def test_login_rejects_unverified_email_as_identifier(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute(
            "UPDATE users SET email=?,email_verified=0 WHERE username='admin'",
            ("unverified@example.com",),
        )
    client.get("/logout")
    response = client.post(
        "/login",
        data={
            "username": "unverified@example.com",
            "password": "test-strong-password-2026",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Accueil".encode() not in response.data


def test_resident_profile_shows_annual_leave_dates_and_balance(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES(?,?,?)",
            ("LeaveProfile", "Resident", 2),
        )
        rid = conn.execute(
            "SELECT id FROM residents WHERE surname='LeaveProfile'"
        ).fetchone()[0]
        year = __import__("datetime").date.today().year
        conn.execute(
            "INSERT INTO leave_years(resident_id,year,earned_days) VALUES(?,?,30)",
            (rid, year),
        )
        conn.execute(
            "INSERT INTO leave_entries(resident_id,start_date,end_date,days,notes) VALUES(?,?,?,?,?)",
            (rid, f"{year}-06-01", f"{year}-06-03", 3, "Annual leave"),
        )
    response = client.get(f"/profile/{rid}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Congés annuels" in html
    assert "Acquis :" in html and "30" in html
    assert "Utilisés :" in html and "3" in html
    assert "Restants :" in html and "27" in html
    assert "Annual leave" in html


def test_resident_profile_shows_external_internship_details(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES(?,?,?)",
            ("AbroadProfile", "Resident", 3),
        )
        rid = conn.execute(
            "SELECT id FROM residents WHERE surname='AbroadProfile'"
        ).fetchone()[0]
        conn.execute(
            """INSERT INTO external_rotations(
                resident_id,supervisor,destination,hospital,country,rotation_type,
                start_date,end_date,notes,status
            ) VALUES(?,?,?,?,?,?,?,?,?,'active')""",
            (
                rid, "Dr Test", "Paris", "Hôpital Test", "France", "Anesthésie",
                "2026-05-01", "2026-06-30", "Stage de perfectionnement",
            ),
        )
    response = client.get(f"/profile/{rid}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Stages à l’étranger" in html
    assert "Hôpital Test" in html
    assert "France" in html
    assert "Dr Test" in html
    assert "2026-05-01" in html
    assert "2026-06-30" in html


def test_email_verification_uses_resimanage_smtp_environment_without_exposing_secret(monkeypatch):
    monkeypatch.setenv("RESIMANAGE_SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("RESIMANAGE_SMTP_PORT", "587")
    monkeypatch.setenv("RESIMANAGE_SMTP_FROM", "noreply@example.test")
    monkeypatch.setenv("RESIMANAGE_SMTP_USER", "mailer@example.test")
    monkeypatch.setenv("RESIMANAGE_SMTP_PASSWORD", "test-secret")
    for name in ("HOST", "PORT", "FROM", "USER"):
        monkeypatch.delenv("RESITRACK_SMTP_" + name, raising=False)
    monkeypatch.delenv("RESITRACK_SMTP_PASSWORD", raising=False)

    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            sent["connection"] = (host, port, timeout)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self):
            sent["tls"] = True

        def login(self, username, password):
            sent["login"] = (username, password)

        def send_message(self, message):
            sent["message"] = message

    monkeypatch.setattr(rotation_app.smtplib, "SMTP", FakeSMTP)
    rotation_app.send_verification_email("resident@example.test", "123456")

    assert sent["connection"] == ("smtp.example.test", 587, 15)
    assert sent["tls"] is True
    assert sent["login"] == ("mailer@example.test", "test-secret")
    assert sent["message"]["To"] == "resident@example.test"
    assert "123456" in sent["message"].get_content()
    assert "test-secret" not in sent["message"].as_string()


def test_email_verification_rejects_invalid_smtp_port(monkeypatch):
    monkeypatch.setenv("RESIMANAGE_SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("RESIMANAGE_SMTP_PORT", "not-a-port")
    monkeypatch.setenv("RESIMANAGE_SMTP_FROM", "noreply@example.test")
    monkeypatch.setenv("RESIMANAGE_SMTP_USER", "mailer@example.test")
    monkeypatch.setenv("RESIMANAGE_SMTP_PASSWORD", "test-secret")

    try:
        rotation_app.send_verification_email("resident@example.test", "123456")
    except RuntimeError as exc:
        assert "SMTP port" in str(exc)
    else:
        raise AssertionError("Invalid SMTP port should be rejected.")


def test_admin_can_change_role_and_reset_password_with_audit(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    client.post("/users", data={
        "username": "account-control-test",
        "password": "old-test-password-2026",
        "role": "user",
    })
    with rotation_app.db() as conn:
        uid = conn.execute(
            "SELECT id FROM users WHERE username='account-control-test'"
        ).fetchone()[0]

    role_response = client.post("/users", data={
        "action": "change_role",
        "user_id": str(uid),
        "new_role": "super_admin",
    }, follow_redirects=True)
    assert role_response.status_code == 200
    with rotation_app.db() as conn:
        assert conn.execute("SELECT role FROM users WHERE id=?", (uid,)).fetchone()[0] == "super_admin"
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE action='user.role_changed'").fetchone()[0] == 1

    new_password = "new-test-password-2026"
    reset_response = client.post("/users", data={
        "action": "reset_password",
        "user_id": str(uid),
        "new_password": new_password,
    }, follow_redirects=True)
    assert reset_response.status_code == 200
    with rotation_app.db() as conn:
        stored = conn.execute("SELECT password_hash FROM users WHERE id=?", (uid,)).fetchone()[0]
        assert rotation_app.verify_password(new_password, stored)
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE action='user.password_reset'").fetchone()[0] == 1
        audit_details = " ".join(
            row[0] for row in conn.execute(
                "SELECT details FROM audit WHERE action='user.password_reset'"
            ).fetchall()
        )
        assert new_password not in audit_details

    client.get("/logout")
    response = client.post("/login", data={
        "username": "account-control-test",
        "password": new_password,
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"account-control-test" not in response.data  # resident-facing UI does not expose admin account data


def test_official_admins_cannot_be_demoted_and_last_super_admin_is_protected(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        official_id = conn.execute(
            "SELECT id FROM users WHERE lower(username)='admin'"
        ).fetchone()[0]

    response = client.post("/users", data={
        "action": "change_role",
        "user_id": str(official_id),
        "new_role": "user",
    }, follow_redirects=True)
    assert response.status_code == 200
    with rotation_app.db() as conn:
        role = conn.execute("SELECT role FROM users WHERE id=?", (official_id,)).fetchone()[0]
        assert role == "super_admin"


def test_windows_launcher_migrates_legacy_database_photos_and_secret_without_deleting_source(tmp_path, monkeypatch):
    import sqlite3
    import windows_launcher as desktop_launcher

    legacy_root = tmp_path / "old-install"
    legacy_root.mkdir()
    legacy_db = legacy_root / "rotation.db"
    with sqlite3.connect(legacy_db) as conn:
        conn.execute("CREATE TABLE migration_probe(value TEXT)")
        conn.execute("INSERT INTO migration_probe(value) VALUES('keep-me')")
    old_secret = "a" * 64
    (legacy_root / ".rotation_secret").write_text(old_secret, encoding="ascii")
    photo_dir = legacy_root / "resident_photos"
    photo_dir.mkdir()
    (photo_dir / "resident_1.jpg").write_bytes(b"test-photo")

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "LocalAppData"))
    monkeypatch.setattr(desktop_launcher.sys, "frozen", True, raising=False)
    monkeypatch.setattr(desktop_launcher.sys, "executable", str(legacy_root / "ResiManage.exe"))

    data_dir = desktop_launcher._prepare_user_data()
    with sqlite3.connect(data_dir / "rotation.db") as conn:
        assert conn.execute("SELECT value FROM migration_probe").fetchone()[0] == "keep-me"
    assert (data_dir / ".rotation_secret").read_text(encoding="ascii") == old_secret
    assert (data_dir / "resident_photos" / "resident_1.jpg").read_bytes() == b"test-photo"
    assert legacy_db.exists()
    assert (legacy_root / "resident_photos" / "resident_1.jpg").exists()


def test_exam_sessions_and_attempts_are_stored_separately_and_remedial_counts_for_progression(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,1)", ("Session", "Resident"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Session'").fetchone()[0]

    for exam_type, attempt, theory, practical in [
        ("virtual", "1", 6, 7),
        ("actual", "1", 9, 9),
        ("remedial", "1", 12, 11),
    ]:
        response = client.post("/exams", data={
            "action": "record",
            "resident": str(rid),
            "study_year": "1",
            "module": "Anesthesia",
            "exam_type": exam_type,
            "attempt": attempt,
            "theory": str(theory),
            "practical": str(practical),
        }, follow_redirects=True)
        assert response.status_code == 200

    with rotation_app.db() as conn:
        rows = conn.execute(
            "SELECT exam_type,attempt,theory,practical FROM exam_records WHERE resident_id=? ORDER BY id",
            (rid,),
        ).fetchall()
        assert [(row["exam_type"], row["attempt"]) for row in rows] == [
            ("virtual", 1), ("actual", 1), ("remedial", 1)
        ]

    response = client.post("/exams", data={
        "action": "evaluate_first_year",
        "resident": str(rid),
        "study_year": "1",
        "all_modules_confirmed": "yes",
    }, follow_redirects=True)
    assert response.status_code == 200
    with rotation_app.db() as conn:
        assert conn.execute("SELECT year FROM residents WHERE id=?", (rid,)).fetchone()[0] == 2


def test_dems_insertion_records_two_mark_components_for_year_four(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,4)", ("Dems", "Resident"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Dems'").fetchone()[0]

    response = client.post("/exams", data={
        "action": "record",
        "resident": str(rid),
        "study_year": "4",
        "module": "DEMS insertion",
        "exam_type": "dems_insertion",
        "attempt": "1",
        "theory": "13.5",
        "practical": "15",
    }, follow_redirects=True)
    assert response.status_code == 200
    with rotation_app.db() as conn:
        row = conn.execute(
            "SELECT theory,practical,exam_type,attempt FROM exam_records WHERE resident_id=?",
            (rid,),
        ).fetchone()
        assert tuple(row) == (13.5, 15.0, "dems_insertion", 1)


def test_first_year_evaluation_blocks_modules_with_only_virtual_marks(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,1)", ("Incomplete", "Sessions"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Incomplete'").fetchone()[0]

    for module, exam_type, theory, practical in [
        ("Module A", "actual", 12, 12),
        ("Module B", "virtual", 18, 18),
    ]:
        client.post("/exams", data={
            "action": "record",
            "resident": str(rid),
            "study_year": "1",
            "module": module,
            "exam_type": exam_type,
            "attempt": "1",
            "theory": str(theory),
            "practical": str(practical),
        })

    response = client.post("/exams", data={
        "action": "evaluate_first_year",
        "resident": str(rid),
        "study_year": "1",
        "all_modules_confirmed": "yes",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "les notes virtuelles seules ne comptent pas".encode() in response.data
    with rotation_app.db() as conn:
        assert conn.execute("SELECT year FROM residents WHERE id=?", (rid,)).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM decisions WHERE details LIKE '%Incomplete Sessions%'").fetchone()[0] == 0


def test_leave_rejects_unknown_resident_without_creating_leave_years(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    response = client.post("/leave", data={
        "resident_id": "987654321",
        "start_date": "2026-11-01",
        "end_date": "2026-11-05",
    }, follow_redirects=True)
    assert response.status_code == 200
    assert "Ce résident n’existe pas".encode() in response.data
    with rotation_app.db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM leave_entries").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM leave_years WHERE resident_id=987654321").fetchone()[0] == 0


def test_exam_form_guides_dems_sessions_to_year_four(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    response = client.get("/exams")
    assert response.status_code == 200
    assert b'id="exam-study-year"' in response.data
    assert b'id="exam-session-type"' in response.data
    assert b'if(!isYearFour&&t.value.indexOf("dems_")===0)t.value="actual"' in response.data
    assert b'if(o.value.indexOf("dems_")===0)o.disabled=!isYearFour' in response.data


def test_resident_profile_displays_exam_session_and_attempt(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,4)", ("ExamSession", "Profile"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='ExamSession'").fetchone()[0]
        conn.execute(
            "INSERT INTO exam_records(resident_id,study_year,module,theory,practical,exam_type,attempt) VALUES(?,?,?,?,?,?,?)",
            (rid, 4, "DEMS insertion", 14, 16, "dems_insertion", 2),
        )
        conn.commit()

    response = client.get(f"/profile/{rid}")
    assert response.status_code == 200
    assert b"DEMS insertion" in response.data
    assert b"dems_insertion" in response.data
    assert b"<td>2</td>" in response.data
    assert b"14.0/20" in response.data
    assert b"16.0/20" in response.data


def test_resident_summary_includes_external_rotation_dates_and_country(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,3)", ("Away", "Resident"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Away'").fetchone()[0]
        conn.execute(
            "INSERT INTO external_rotations(resident_id,supervisor,destination,hospital,country,rotation_type,start_date,end_date,status) VALUES(?,?,?,?,?,?,?,?,?)",
            (rid, "Dr Supervisor", "Paris", "Hôpital Test", "France", "Réanimation", "2026-11-01", "2026-12-01", "active"),
        )
        conn.commit()

    response = client.get("/summary")
    assert response.status_code == 200
    assert "Hôpital Test".encode("utf-8") in response.data
    assert b"France" in response.data
    assert b"2026-11-01" in response.data
    assert b"2026-12-01" in response.data


def test_external_internship_request_requires_admin_approval_before_blocking_assignments(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,?,?)",
            ("Request", "Resident", 2, "active"),
        )
        rid = conn.execute("SELECT id FROM residents WHERE surname='Request'").fetchone()[0]
        period = conn.execute(
            "SELECT id,year_label,name FROM periods WHERE name='Période 3'"
        ).fetchone()
        assert period is not None
        tid = conn.execute(
            "SELECT id FROM terrains WHERE name='Réanimation chirurgicale'"
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO assignments(resident_id,terrain_id,period_id,status) VALUES(?,?,?,'confirmed')",
            (rid, tid, period["id"]),
        )
        conn.execute(
            "INSERT INTO users(username,password_hash,role,active) VALUES(?,?,?,1)",
            ("internrequester", rotation_app.hash_password("requester-test-password"), "user"),
        )
        conn.commit()

    # A standard account submits the request, but it must not become an approved blocking stage.
    with client.session_transaction() as sess:
        sess["user"] = "internrequester"
        sess["role"] = "user"
    request_response = client.post("/external-rotations", data={
        "resident_id": str(rid),
        "supervisor": "Dr Request",
        "destination": "Alger",
        "hospital": "CHU Request",
        "country": "Algeria",
        "rotation_type": "Clinical",
        "start_date": "2026-08-10",
        "end_date": "2026-08-20",
        "notes": "Request awaiting authorization",
    }, follow_redirects=True)
    assert request_response.status_code == 200
    with rotation_app.db() as conn:
        row = conn.execute(
            "SELECT id,request_status,status FROM external_rotations WHERE resident_id=?",
            (rid,),
        ).fetchone()
        assert tuple(row[1:]) == ("pending", "requested")
        with rotation_app.app.test_request_context("/"):
            allowed, message, _ = rotation_app.check(conn, rid, tid, period["id"], period["year_label"])
        assert "External rotation blocks" not in message

    # The Super Admin cannot approve a request that conflicts with an existing local assignment.
    login(client)
    denied_approval = client.post(
        f"/external-rotations/{row['id']}/decision",
        data={"decision": "approve"},
        follow_redirects=True,
    )
    assert denied_approval.status_code == 200
    assert "Le stage à l’étranger chevauche une affectation locale existante".encode() in denied_approval.data
    with rotation_app.db() as conn:
        assert conn.execute(
            "SELECT request_status FROM external_rotations WHERE id=?", (row["id"],)
        ).fetchone()[0] == "pending"
        conn.execute("UPDATE assignments SET status='cancelled' WHERE resident_id=? AND period_id=?", (rid, period["id"]))
        conn.commit()

    approved = client.post(
        f"/external-rotations/{row['id']}/decision",
        data={"decision": "approve"},
        follow_redirects=True,
    )
    assert approved.status_code == 200
    with rotation_app.db() as conn:
        saved = conn.execute(
            "SELECT request_status,status FROM external_rotations WHERE id=?", (row["id"],)
        ).fetchone()
        assert tuple(saved) == ("approved", "returned")
        with rotation_app.app.test_request_context("/"):
            allowed, message, _ = rotation_app.check(conn, rid, tid, period["id"], period["year_label"])
        assert allowed is False
        assert "External rotation blocks local assignment" in message
        assert conn.execute(
            "SELECT COUNT(*) FROM audit WHERE action='external_rotation.request_approved'"
        ).fetchone()[0] == 1


def test_sync_change_journal_records_business_row_versions_and_tombstones(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)  # Initializes schema and journal triggers.
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,?,?)",
            ("Journal", "Resident", 1, "active"),
        )
        rid = conn.execute("SELECT id FROM residents WHERE surname='Journal'").fetchone()[0]
        conn.execute("UPDATE residents SET surname=? WHERE id=?", ("JournalUpdated", rid))
        conn.execute("DELETE FROM residents WHERE id=?", (rid,))
        # Credentials are deliberately outside the syncable entity set.
        conn.execute(
            "INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
            ("sync-secret-test", "not-a-real-secret-hash", "user"),
        )
        conn.commit()
        rows = conn.execute(
            "SELECT operation,payload_json FROM sync_change_log WHERE entity='residents' AND entity_id=? ORDER BY seq",
            (str(rid),),
        ).fetchall()
        entities = {row[0] for row in conn.execute("SELECT DISTINCT entity FROM sync_change_log")}
    assert [row["operation"] for row in rows] == ["upsert", "upsert", "delete"]
    assert json.loads(rows[0]["payload_json"])["surname"] == "Journal"
    assert json.loads(rows[1]["payload_json"])["surname"] == "JournalUpdated"
    assert json.loads(rows[2]["payload_json"]) == {"id": rid}
    assert "users" not in entities


def test_windows_sync_listener_requires_exact_vpn_ip_and_tls(monkeypatch, tmp_path):
    import windows_launcher as desktop_launcher

    monkeypatch.delenv("RESIMANAGE_BIND", raising=False)
    monkeypatch.delenv("RESIMANAGE_PORT", raising=False)
    monkeypatch.delenv("RESIMANAGE_TLS_CERT", raising=False)
    monkeypatch.delenv("RESIMANAGE_TLS_KEY", raising=False)
    assert desktop_launcher._server_settings() == ("127.0.0.1", 0, None)

    monkeypatch.setenv("RESIMANAGE_BIND", "10.55.0.8")
    with pytest.raises(RuntimeError, match="requires TLS"):
        desktop_launcher._server_settings()

    cert = tmp_path / "vpn-cert.pem"
    key = tmp_path / "vpn-key.pem"
    cert.write_text("test-cert", encoding="ascii")
    key.write_text("test-key", encoding="ascii")
    monkeypatch.setenv("RESIMANAGE_TLS_CERT", str(cert))
    monkeypatch.setenv("RESIMANAGE_TLS_KEY", str(key))
    monkeypatch.setenv("RESIMANAGE_PORT", "5443")
    assert desktop_launcher._server_settings() == ("10.55.0.8", 5443, (str(cert), str(key)))

    monkeypatch.setenv("RESIMANAGE_BIND", "0.0.0.0")
    with pytest.raises(RuntimeError, match="Wildcard binds"):
        desktop_launcher._server_settings()
    monkeypatch.setenv("RESIMANAGE_BIND", "8.8.8.8")
    with pytest.raises(RuntimeError, match="private/VPN IP"):
        desktop_launcher._server_settings()


def test_sync_device_enrollment_api_pull_tls_guard_and_revocation(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    enrolled = client.post("/sync-devices", data={
        "action": "enroll", "label": "Test resident phone"
    }, follow_redirects=True)
    assert enrolled.status_code == 200
    match = re.search(rb"<p><code>([A-Za-z0-9_-]{40,})</code></p>", enrolled.data)
    assert match, enrolled.data.decode("utf-8", errors="replace")
    token = match.group(1).decode("ascii")
    assert "Copiez ce jeton maintenant".encode() in enrolled.data
    with client.session_transaction() as sess:
        assert "issued_sync_device" not in sess

    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,?,?)",
            ("ApiPull", "Resident", 1, "active"),
        )
        rid = conn.execute("SELECT id FROM residents WHERE surname='ApiPull'").fetchone()[0]
        device = conn.execute(
            "SELECT device_id,token_hash,active FROM sync_devices WHERE label=?",
            ("Test resident phone",),
        ).fetchone()
        assert device["token_hash"] == hashlib.sha256(token.encode("ascii")).hexdigest()
        assert device["active"] == 1
        conn.commit()

    assert client.get("/api/sync/v1/status").status_code == 401
    headers = {"Authorization": "Bearer " + token}
    status = client.get("/api/sync/v1/status", headers=headers)
    assert status.status_code == 200
    assert status.json["device_id"] == device["device_id"]
    assert status.json["push_enabled"] is False
    readonly_push = client.post("/api/sync/v1/push", headers=headers, json={"operations":[{}]})
    assert readonly_push.status_code == 403

    bootstrap = client.get("/api/sync/v1/bootstrap?entity=residents&limit=50", headers=headers)
    assert bootstrap.status_code == 200
    assert any(row["id"] == rid for row in bootstrap.json["rows"])
    pull = client.get("/api/sync/v1/pull?after_seq=0&limit=500", headers=headers)
    assert pull.status_code == 200
    assert any(change["entity"] == "residents" and change["entity_id"] == str(rid)
               for change in pull.json["changes"])

    remote_http = client.get(
        "/api/sync/v1/status",
        headers=headers,
        environ_base={"REMOTE_ADDR": "10.55.0.9"},
    )
    assert remote_http.status_code == 426

    revoked = client.post("/sync-devices", data={
        "action": "revoke", "device_id": device["device_id"]
    }, follow_redirects=True)
    assert revoked.status_code == 200
    assert client.get("/api/sync/v1/status", headers=headers).status_code == 401


def test_sync_write_device_push_is_idempotent_conflict_aware_and_downgrades_assignments(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    enrolled = client.post("/sync-devices", data={
        "action": "enroll", "label": "Trusted sync writer", "mode": "read_write"
    }, follow_redirects=True)
    match = re.search(rb"<p><code>([A-Za-z0-9_-]{40,})</code></p>", enrolled.data)
    assert match
    token = match.group(1).decode("ascii")
    headers = {"Authorization": "Bearer " + token}
    status = client.get("/api/sync/v1/status", headers=headers)
    assert status.status_code == 200 and status.json["push_enabled"] is True
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,?,?)",
            ("Push", "Resident", 2, "active"),
        )
        rid = conn.execute("SELECT id FROM residents WHERE surname='Push'").fetchone()[0]
        resident_fields = rotation_app._SYNC_ENTITY_FIELDS["residents"]
        resident_row = conn.execute("SELECT * FROM residents WHERE id=?", (rid,)).fetchone()
        resident_payload = {field: resident_row[field] for field in resident_fields}
        terrain_id = conn.execute(
            "SELECT id FROM terrains WHERE name='Réanimation chirurgicale'"
        ).fetchone()[0]
        period = conn.execute("SELECT id,year_label,name FROM periods ORDER BY id LIMIT 1").fetchone()
        conn.commit()
    # The fixture inserted this resident on the server; use its current cursor for the test update.
    base_seq = client.get("/api/sync/v1/status", headers=headers).json["server_cursor"]

    resident_payload["surname"] = "PushedUpdate"
    operation = {
        "op_id": "resident-push-op-0001", "entity": "residents",
        "entity_id": str(rid), "operation": "upsert",
        "base_seq": base_seq, "payload": resident_payload,
    }
    pushed = client.post("/api/sync/v1/push", headers=headers, json={"operations":[operation]})
    assert pushed.status_code == 200, pushed.data
    assert pushed.json["results"][0]["status"] == "applied"
    with rotation_app.db() as conn:
        assert conn.execute("SELECT surname FROM residents WHERE id=?", (rid,)).fetchone()[0] == "PushedUpdate"

    replay = client.post("/api/sync/v1/push", headers=headers, json={"operations":[operation]})
    assert replay.status_code == 200
    assert replay.json["results"][0]["replayed"] is True

    with rotation_app.db() as conn:
        conn.execute("UPDATE residents SET surname='ServerUpdate' WHERE id=?", (rid,))
        conn.commit()
        terrain_id = conn.execute("SELECT id FROM terrains WHERE name='Réanimation chirurgicale'").fetchone()[0]
        period = conn.execute("SELECT id,year_label,name FROM periods ORDER BY id LIMIT 1").fetchone()
        assignment_payload = {
            "id": 987654, "resident_id": rid, "terrain_id": terrain_id,
            "period_id": period["id"], "status": "confirmed",
        }
    conflict_op = dict(operation, op_id="resident-push-op-0002", base_seq=base_seq,
                       payload=dict(resident_payload, surname="StaleClient"))
    conflict = client.post("/api/sync/v1/push", headers=headers, json={"operations":[conflict_op]})
    assert conflict.status_code == 200
    assert conflict.json["results"][0]["status"] == "conflict"
    with rotation_app.db() as conn:
        assert conn.execute("SELECT surname FROM residents WHERE id=?", (rid,)).fetchone()[0] == "ServerUpdate"

    assignment_op = {
        "op_id": "assignment-push-op-0001", "entity": "assignments",
        "entity_id": str(assignment_payload["id"]), "operation": "upsert",
        "base_seq": conflict.json["results"][0]["server_seq"],
        "payload": assignment_payload,
    }
    assignment_push = client.post("/api/sync/v1/push", headers=headers, json={"operations":[assignment_op]})
    assert assignment_push.status_code == 200
    assert assignment_push.json["results"][0]["status"] == "applied"
    with rotation_app.db() as conn:
        assert conn.execute("SELECT status FROM assignments WHERE id=?", (assignment_payload["id"],)).fetchone()[0] == "pending"



def test_sync_external_rotation_request_rejects_overlap_with_local_assignment(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,?,?)",
            ("SyncExternal", "Resident", 2, "active"),
        )
        rid = conn.execute("SELECT id FROM residents WHERE surname='SyncExternal'").fetchone()[0]
        terrain_id = conn.execute("SELECT id FROM terrains WHERE name='Réanimation chirurgicale'").fetchone()[0]
        period = conn.execute(
            "SELECT id FROM periods WHERE year_label LIKE '2026-%' AND name='Période 1' LIMIT 1"
        ).fetchone()
        assert period is not None
        conn.execute(
            "INSERT INTO assignments(resident_id,terrain_id,period_id,status) VALUES(?,?,?,'confirmed')",
            (rid, terrain_id, period["id"]),
        )
        payload = {
            "id": 8101, "resident_id": rid, "supervisor": "Supervisor",
            "destination": "Foreign internship", "hospital": "Teaching Hospital",
            "country": "France", "rotation_type": "anesthesia",
            "start_date": "2026-03-01", "end_date": "2026-03-31",
            "notes": "overlap must be blocked", "status": "requested",
            "request_status": "pending", "created_by": "test",
            "created_at": "2026-10-20 00:00:00", "updated_at": "2026-10-20 00:00:00",
        }
        with pytest.raises(ValueError, match="Le stage à l’étranger chevauche une affectation locale existante"):
            rotation_app._validate_sync_push_row(conn, "external_rotations", payload)

def test_sync_push_leave_validation_supports_cross_year_leave_and_rejects_overlap(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,?,?)",
            ("CrossYearLeave", "Resident", 2, "active"),
        )
        rid = conn.execute("SELECT id FROM residents WHERE surname='CrossYearLeave'").fetchone()[0]
        conn.execute(
            "INSERT INTO leave_years(resident_id,year,earned_days) VALUES(?,?,?)",
            (rid, 2026, 30),
        )
        conn.execute(
            "INSERT INTO leave_years(resident_id,year,earned_days) VALUES(?,?,?)",
            (rid, 2027, 30),
        )
        fields = rotation_app._SYNC_ENTITY_FIELDS["leave_entries"]
        payload = {
            "id": 7001, "resident_id": rid, "start_date": "2026-12-28",
            "end_date": "2027-01-03", "days": 7, "notes": "cross-year leave",
            "created_by": "test", "created_at": "2026-10-20 00:00:00",
        }
        validated = rotation_app._validate_sync_push_row(conn, "leave_entries", payload)
        assert validated["days"] == 7
        conn.execute(
            "INSERT INTO leave_entries(id,resident_id,start_date,end_date,days,notes,created_by) VALUES(?,?,?,?,?,?,?)",
            (7002, rid, "2026-12-30", "2027-01-01", 3, "existing leave", "test"),
        )
        with pytest.raises(ValueError, match="overlaps an existing entry"):
            rotation_app._validate_sync_push_row(conn, "leave_entries", payload)


def test_android_sync_client_rejects_invalid_private_ca_certificate(tmp_path):
    with pytest.raises(sync_client.SyncError, match="PEM"):
        sync_client._configure_ca(tmp_path, "not a certificate")
    assert not (tmp_path / "resimanage_sync_ca.pem").exists()


def test_android_sync_client_requires_https_and_remote_apply_does_not_echo(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    valid_url, token = sync_client._validate_config("https://10.55.0.8:5000", "T" * 43)
    assert valid_url == "https://10.55.0.8:5000"
    assert len(token) == 43
    with pytest.raises(sync_client.SyncError, match="HTTPS"):
        sync_client._validate_config("http://10.55.0.8:5000", "T" * 43)

    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,?,?)",
            ("SyncClient", "Resident", 1, "active"),
        )
        rid = conn.execute("SELECT id FROM residents WHERE surname='SyncClient'").fetchone()[0]
        fields = rotation_app._SYNC_ENTITY_FIELDS["residents"]
        row = conn.execute("SELECT * FROM residents WHERE id=?", (rid,)).fetchone()
        payload = {field: row[field] for field in fields}
        local_seq_before = conn.execute("SELECT COALESCE(MAX(seq),0) FROM sync_change_log").fetchone()[0]
        conn.commit()

    payload["surname"] = "ServerPulled"
    conn = rotation_app.db()
    sync_client._apply_remote_batch(conn, [{
        "seq": 500, "entity": "residents", "entity_id": str(rid),
        "operation": "upsert", "payload": payload,
    }], "https://sync.example.test", "T" * 43, str(tmp_path))
    assert conn.execute("SELECT surname FROM residents WHERE id=?", (rid,)).fetchone()[0] == "ServerPulled"
    assert conn.execute("SELECT COALESCE(MAX(seq),0) FROM sync_change_log").fetchone()[0] == local_seq_before
    assert conn.execute("SELECT server_seq FROM sync_row_versions WHERE entity='residents' AND entity_id=?", (str(rid),)).fetchone()[0] == 500
    conn.execute("UPDATE residents SET surname='LocalEditedAfterPull' WHERE id=?", (rid,))
    conn.commit()
    latest = conn.execute(
        "SELECT base_seq FROM sync_change_log WHERE entity='residents' AND entity_id=? ORDER BY seq DESC LIMIT 1",
        (str(rid),),
    ).fetchone()[0]
    assert latest == 500
    conn.close()



def test_android_sync_pull_uses_explicit_data_directory(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,?,?)",
            ("SyncPull", "Resident", 1, "active"),
        )
        rid = conn.execute("SELECT id FROM residents WHERE surname='SyncPull'").fetchone()[0]
        fields = rotation_app._SYNC_ENTITY_FIELDS["residents"]
        row = conn.execute("SELECT * FROM residents WHERE id=?", (rid,)).fetchone()
        payload = {field: row[field] for field in fields}
        conn.commit()
    payload["surname"] = "PulledFromServer"
    monkeypatch.setattr(sync_client, "_api", lambda *args, **kwargs: {
        "changes": [{
            "seq": 900, "entity": "residents", "entity_id": str(rid),
            "operation": "upsert", "payload": payload,
        }],
        "next_seq": 900,
        "has_more": False,
    })
    conn = rotation_app.db()
    cursor, total = sync_client._pull_all(
        conn, "https://sync.example.test", "T" * 43, 0, str(tmp_path)
    )
    assert (cursor, total) == (900, 1)
    assert conn.execute("SELECT surname FROM residents WHERE id=?", (rid,)).fetchone()[0] == "PulledFromServer"
    conn.close()



def test_android_sync_bootstrap_uses_explicit_data_directory(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,?,?)",
            ("Bootstrap", "Resident", 1, "active"),
        )
        rid = conn.execute("SELECT id FROM residents WHERE surname='Bootstrap'").fetchone()[0]
        fields = rotation_app._SYNC_ENTITY_FIELDS["residents"]
        row = conn.execute("SELECT * FROM residents WHERE id=?", (rid,)).fetchone()
        payload = {field: row[field] for field in fields}
        conn.execute("DELETE FROM residents WHERE id=?", (rid,))
        conn.commit()
    def fake_api(base_url, token, path, body=None):
        if "/bootstrap?" in path and "entity=residents" in path:
            return {"rows": [payload], "next_id": rid, "has_more": False}
        if "/bootstrap?" in path:
            return {"rows": [], "next_id": 0, "has_more": False}
        raise AssertionError("Unexpected sync request: " + path)
    monkeypatch.setattr(sync_client, "_api", fake_api)
    conn = rotation_app.db()
    sync_client._bootstrap_empty_device(
        conn, "https://sync.example.test", "T" * 43, 750, str(tmp_path)
    )
    assert conn.execute("SELECT surname FROM residents WHERE id=?", (rid,)).fetchone()[0] == "Bootstrap"
    assert conn.execute(
        "SELECT value FROM settings WHERE key='resimanage_sync_remote_cursor'"
    ).fetchone()[0] == "750"
    conn.close()



def test_android_sync_bootstrap_refuses_to_overwrite_local_objectives(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        terrain_id = conn.execute("SELECT id FROM terrains ORDER BY id LIMIT 1").fetchone()[0]
        conn.execute(
            "INSERT INTO objectives(terrain_id,study_year,objective,completed) VALUES(?,1,?,0)",
            (terrain_id, "Locally configured objective"),
        )
        conn.commit()
    monkeypatch.setattr(
        sync_client, "_api",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("network must not start")),
    )
    conn = rotation_app.db()
    with pytest.raises(sync_client.SyncError, match="empty device data database"):
        sync_client._bootstrap_empty_device(
            conn, "https://sync.example.test", "T" * 43, 750, str(tmp_path)
        )
    assert conn.execute(
        "SELECT objective FROM objectives WHERE terrain_id=?",
        (terrain_id,),
    ).fetchone()[0] == "Locally configured objective"
    conn.close()


def test_sync_api_transfers_resident_photo_with_write_token_and_version_guard(tmp_path, monkeypatch):
    from PIL import Image

    client = setup_client(tmp_path, monkeypatch)
    login(client)
    enrolled = client.post("/sync-devices", data={
        "action": "enroll", "label": "Photo sync device", "mode": "read_write"
    }, follow_redirects=True)
    match = re.search(rb"<p><code>([A-Za-z0-9_-]{40,})</code></p>", enrolled.data)
    assert match
    headers = {"Authorization": "Bearer " + match.group(1).decode("ascii")}
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year,status,photo_path) VALUES(?,?,?,?,?)",
            ("PhotoSync", "Resident", 1, "active", ""),
        )
        rid = conn.execute("SELECT id FROM residents WHERE surname='PhotoSync'").fetchone()[0]
        conn.commit()
    base_seq = client.get("/api/sync/v1/status", headers=headers).json["server_cursor"]

    source = io.BytesIO()
    Image.new("RGB", (48, 32), "white").save(source, format="PNG")
    uploaded = client.put(
        f"/api/sync/v1/photo/{rid}?base_seq={base_seq}",
        data=source.getvalue(), headers=headers, content_type="image/png",
    )
    assert uploaded.status_code == 200, uploaded.data
    assert uploaded.json["photo_path"].startswith("/photos/resident_")
    photo = client.get(f"/api/sync/v1/photo/{rid}", headers=headers)
    assert photo.status_code == 200
    assert photo.mimetype == "image/webp"
    assert len(photo.data) > 0

    # A network retry of the same photo is idempotent before any newer row edit.
    replay = client.put(
        f"/api/sync/v1/photo/{rid}?base_seq={base_seq}",
        data=source.getvalue(), headers=headers, content_type="image/png",
    )
    assert replay.status_code == 200, replay.data
    assert replay.json["replayed"] is True
    assert replay.json["photo_path"] == uploaded.json["photo_path"]

    with rotation_app.db() as conn:
        saved = conn.execute("SELECT photo_path FROM residents WHERE id=?", (rid,)).fetchone()[0]
        assert saved == uploaded.json["photo_path"]
        assert (tmp_path / "resident_photos" / os.path.basename(saved)).is_file()
        conn.execute("UPDATE residents SET surname='PhotoSyncServerEdit' WHERE id=?", (rid,))
        conn.commit()
    stale_upload = client.put(
        f"/api/sync/v1/photo/{rid}?base_seq={base_seq}",
        data=source.getvalue(), headers=headers, content_type="image/png",
    )
    assert stale_upload.status_code == 409



def test_android_sync_uploads_photo_when_resident_upsert_result_is_replayed(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    photo_dir = tmp_path / "resident_photos"
    photo_dir.mkdir()
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year,status) VALUES(?,?,?,?)",
            ("PhotoRetry", "Resident", 1, "active"),
        )
        rid = conn.execute("SELECT id FROM residents WHERE surname='PhotoRetry'").fetchone()[0]
        filename = "resident_%s_retry.png" % rid
        (photo_dir / filename).write_bytes(b"local-photo-bytes")
        conn.execute("UPDATE residents SET photo_path=? WHERE id=?", ("/photos/" + filename, rid))
        conn.commit()

    upload_calls = []
    def fake_api(base_url, token, path, body=None):
        assert path == "/api/sync/v1/push"
        assert body and len(body["operations"]) == 1
        op = body["operations"][0]
        assert op["entity"] == "residents"
        return {"results": [{
            "op_id": op["op_id"], "status": "applied", "server_seq": 42, "replayed": True,
        }]}
    def fake_put(base_url, token, path, raw, mime):
        upload_calls.append((path, raw, mime))
        return {"ok": True, "server_seq": 43}
    monkeypatch.setattr(sync_client, "_api", fake_api)
    monkeypatch.setattr(sync_client, "_api_put_bytes", fake_put)

    conn = rotation_app.db()
    result = sync_client._push_local_changes(
        conn, "https://sync.example.test", "T" * 43, "device-retry", 0, str(tmp_path)
    )
    assert result["pushed"] == 1
    assert len(upload_calls) == 1
    assert upload_calls[0][0].startswith("/api/sync/v1/photo/%s?base_seq=42" % rid)
    assert upload_calls[0][1] == b"local-photo-bytes"
    assert upload_calls[0][2] == "image/png"
    assert conn.execute("SELECT server_seq FROM sync_row_versions WHERE entity='residents' AND entity_id=?", (str(rid),)).fetchone()[0] == 43
    conn.close()


def test_android_sync_client_downloads_remote_photo_to_local_profile_path(tmp_path, monkeypatch):
    from PIL import Image

    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year,status,photo_path) VALUES(?,?,?,?,?)",
            ("PhotoPull", "Resident", 1, "active", ""),
        )
        rid = conn.execute("SELECT id FROM residents WHERE surname='PhotoPull'").fetchone()[0]
        fields = rotation_app._SYNC_ENTITY_FIELDS["residents"]
        row = conn.execute("SELECT * FROM residents WHERE id=?", (rid,)).fetchone()
        payload = {field: row[field] for field in fields}
        local_seq_before = conn.execute("SELECT COALESCE(MAX(seq),0) FROM sync_change_log").fetchone()[0]
        conn.commit()

    image_bytes = io.BytesIO()
    Image.new("RGB", (20, 20), "blue").save(image_bytes, format="WEBP")
    monkeypatch.setattr(sync_client, "_api_bytes", lambda *args: (image_bytes.getvalue(), "image/webp"))
    payload["photo_path"] = "/photos/resident_%s_server.webp" % rid
    conn = rotation_app.db()
    sync_client._apply_remote_batch(conn, [{
        "seq": 700, "entity": "residents", "entity_id": str(rid),
        "operation": "upsert", "payload": payload,
    }], "https://sync.example.test", "T" * 43, str(tmp_path))
    local_path = conn.execute("SELECT photo_path FROM residents WHERE id=?", (rid,)).fetchone()[0]
    assert local_path.startswith("/photos/resident_%s_sync_700" % rid)
    assert (tmp_path / "resident_photos" / os.path.basename(local_path)).is_file()
    assert conn.execute("SELECT COALESCE(MAX(seq),0) FROM sync_change_log").fetchone()[0] == local_seq_before
    assert conn.execute("SELECT server_seq FROM sync_row_versions WHERE entity='residents' AND entity_id=?", (str(rid),)).fetchone()[0] == 700
    conn.close()

def test_rotation_board_route_loads_without_server_error(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)

    response = client.get("/rotation-board")

    assert response.status_code == 200
    assert b"rotation" in response.data.lower() or b"\xd8\xac\xd8\xaf\xd9\x88\xd9\x84" in response.data

def test_postgraduate_year_options_include_exam_and_decision_history(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    conn = rotation_app.db()
    try:
        conn.execute(
            "INSERT INTO residents(surname,firstname,year) VALUES(?,?,?)",
            ("YearSource", "Resident", 2),
        )
        rid = conn.execute(
            "SELECT id FROM residents WHERE surname='YearSource'"
        ).fetchone()["id"]
        conn.execute(
            "INSERT INTO exam_records(resident_id,study_year,module,theory,practical,postgrad_year) VALUES(?,?,?,?,?,?)",
            (rid, 2, "Test module", 12, 13, "2028-2029"),
        )
        conn.execute(
            "INSERT INTO decisions(details,decision,reason,actor,postgrad_year) VALUES(?,?,?,?,?)",
            ("Historical promotion decision", "Approved", "Test", "test-admin", "2029-2030"),
        )
        conn.commit()
        years = rotation_app.available_postgrad_years(conn)
        assert "2028-2029" in years
        assert "2029-2030" in years
    finally:
        conn.close()

def test_rotation_board_updates_occupancy_after_assignment_and_uses_readable_contrast(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)

    with rotation_app.db() as conn:
        conn.execute(
            "INSERT INTO residents(surname, firstname, year) VALUES(?,?,?)",
            ("BoardCount", "Resident", 3),
        )
        rid = conn.execute(
            "SELECT id FROM residents WHERE surname='BoardCount'"
        ).fetchone()["id"]
        terrain_id = conn.execute(
            "SELECT id FROM terrains WHERE name='Réanimation chirurgicale'"
        ).fetchone()["id"]
        period = conn.execute("SELECT id, year_label FROM periods ORDER BY id LIMIT 1").fetchone()
        conn.execute(
            "INSERT INTO capacities(year_label, terrain_id, period_id, places) VALUES(?,?,?,4)",
            (period["year_label"], terrain_id, period["id"]),
        )

    response = client.get("/rotation-board")
    assert response.status_code == 200
    assert "Places occupées : <strong>0</strong> / 4".encode("utf-8") in response.data

    assigned = client.post(
        "/rotation-board",
        data={
            "action": "assign",
            "year": period["year_label"],
            "terrain_id": str(terrain_id),
            "period_id": str(period["id"]),
            "resident_id": str(rid),
            "force_rules": "1",
        },
        follow_redirects=True,
    )
    assert assigned.status_code == 200
    assert b"BoardCount Resident" in assigned.data
    assert "Places occupées : <strong>1</strong> / 4".encode("utf-8") in assigned.data
    assert b".rt-board-table td{color:#10263a!important;background-color:#f8fbff}" in assigned.data
    assert b".rt-board-cell-form input,.rt-board-cell-form select{color:#10263a!important;background:#fff!important" in assigned.data

