import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as rotation_app


def setup_client(tmp_path, monkeypatch):
    monkeypatch.setenv("ROTATION_INITIAL_PASSWORD", "test-strong-password-2026")
    monkeypatch.setattr(rotation_app, "DB", str(tmp_path / "test_rotation.db"))
    monkeypatch.setattr(rotation_app.app, "_ready", False, raising=False)
    rotation_app.app.config.update(TESTING=True, SECRET_KEY="test-only-secret")
    return rotation_app.app.test_client()


def login(client):
    return client.post("/login", data={"password": "test-strong-password-2026"}, follow_redirects=True)


def test_login_page_and_language_selector(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    response = client.get("/login")
    assert response.status_code == 200
    assert "Français".encode() in response.data
    assert "English".encode() in response.data


def test_login_and_protected_dashboard(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    response = login(client)
    assert response.status_code == 200
    assert "Resident".encode() in response.data or "المقيمون".encode() in response.data
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
    assert {"Sédation", "Maxillo-faciale", "CAC DBK", "Brûlés", "Chirurgie cardiaque"} <= optional
    assert "Gynécologie" not in optional


def test_assignment_requires_capacity_and_blocks_same_period_duplicate(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
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
            assert "التربص منجز سابقاً" in message

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
    assert "يمكن التكرار" in message

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
    client.post("/exams", data={"action":"evaluate_first_year","resident":str(rid),"study_year":"1"})
    with rotation_app.db() as conn:
        assert conn.execute("SELECT year FROM residents WHERE id=?", (rid,)).fetchone()[0] == 2
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,1)", ("Fail", "Resident"))
        fail_id = conn.execute("SELECT id FROM residents WHERE surname='Fail'").fetchone()[0]
    for module, theory, practical in [("Module A", 15, 15), ("Module B", 9, 16)]:
        client.post("/exams", data={"action":"record","resident":str(fail_id),"study_year":"1","module":module,"theory":str(theory),"practical":str(practical)})
    client.post("/exams", data={"action":"evaluate_first_year","resident":str(fail_id),"study_year":"1"})
    with rotation_app.db() as conn:
        assert conn.execute("SELECT year FROM residents WHERE id=?", (fail_id,)).fetchone()[0] == 1


def test_dems_archive_keeps_resident_and_history(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,4)", ("Graduate", "Resident"))
        rid = conn.execute("SELECT id FROM residents WHERE surname='Graduate'").fetchone()[0]
        tid = conn.execute("SELECT id FROM terrains WHERE name='Urologie'").fetchone()[0]
        conn.execute("INSERT INTO history(resident_id,terrain_id,year_label,period,date_done) VALUES(?,?,?,?,?)",
                     (rid, tid, "2025-2026", "01 Mai - 30 Juillet", "2025-07-30"))
    response = client.post("/dems", data={"resident":str(rid),"success_date":"2026-10-01"}, follow_redirects=True)
    assert response.status_code == 200
    with rotation_app.db() as conn:
        row = conn.execute("SELECT status,dems_status FROM residents WHERE id=?", (rid,)).fetchone()
        assert tuple(row) == ("graduated", "success")
        assert conn.execute("SELECT COUNT(*) FROM history WHERE resident_id=?", (rid,)).fetchone()[0] == 1
        archive = conn.execute("SELECT history_json FROM dems_archive WHERE resident_id=?", (rid,)).fetchone()
        assert "Urologie" in archive["history_json"]


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

def test_backup_and_restore_preserve_a_recoverable_database(tmp_path, monkeypatch):
    client = setup_client(tmp_path, monkeypatch)
    login(client)
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,?)", ("BeforeBackup", "Resident", 2))
    backup_response = client.get("/backup")
    assert backup_response.status_code == 200
    backup_bytes = backup_response.get_data()
    assert backup_bytes.startswith(b"SQLite format 3")
    with rotation_app.db() as conn:
        conn.execute("INSERT INTO residents(surname,firstname,year) VALUES(?,?,?)", ("AddedAfterBackup", "Resident", 1))
    restored = client.post("/restore", data={
        "backup_file": (io.BytesIO(backup_bytes), "rotation_backup.db")
    }, content_type="multipart/form-data", follow_redirects=True)
    assert restored.status_code == 200
    with rotation_app.db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM residents WHERE surname='BeforeBackup'").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM residents WHERE surname='AddedAfterBackup'").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM audit WHERE action='database.restored'").fetchone()[0] == 1
    assert list(tmp_path.glob("rotation_backup_before_restore_*.db"))

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
