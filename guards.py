# -*- coding: utf-8 -*-
"""Gestion des gardes : historique importé, calendrier mensuel et rapprochement contrôlé."""
import calendar
import hashlib
import json
import os
import re
import unicodedata
from datetime import date
from flask import request, redirect, flash, session, send_file
import io
import csv
import html

SECTORS = ("UMC", "Réanimation chirurgicale")
HOURS = ("16H-08H", "08H-08H")
SOURCE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "gardes_octobre_2026.json")
MONTH_NAMES = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre")
WEEKDAYS = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")


def _valid_month(value):
    return bool(re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", str(value or "")))


def _month_label(value):
    year, month = map(int, value.split("-"))
    return f"{MONTH_NAMES[month - 1].capitalize()} {year}"


def _eligible_residents(c):
    # DEMS/archive and external residents are intentionally excluded.
    return c.execute("""
        SELECT r.id,r.surname,r.firstname,r.year
        FROM residents r
        WHERE r.status='active' AND r.year BETWEEN 1 AND 4
          AND COALESCE(r.resident_type,'local')='local'
          AND COALESCE(r.dems_status,'')<>'preparing'
          AND NOT EXISTS (SELECT 1 FROM dems_archive d WHERE d.resident_id=r.id)
        ORDER BY r.year DESC,r.surname COLLATE NOCASE,r.firstname COLLATE NOCASE
    """).fetchall()


def _dems_preparation_residents(c):
    return c.execute("""
        SELECT r.id,r.surname,r.firstname,r.year,r.dems_status
        FROM residents r
        WHERE r.status='active' AND r.year=4
          AND COALESCE(r.resident_type,'local')='local'
          AND COALESCE(r.dems_status,'')='preparing'
          AND NOT EXISTS (SELECT 1 FROM dems_archive d WHERE d.resident_id=r.id)
        ORDER BY r.surname COLLATE NOCASE,r.firstname COLLATE NOCASE
    """).fetchall()


def _normalise(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def _ensure_schema(c, audit_event):
    c.executescript("""
      CREATE TABLE IF NOT EXISTS guard_sources(
        id INTEGER PRIMARY KEY,
        month TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        filename TEXT NOT NULL,
        source_sha256 TEXT NOT NULL,
        raw_json TEXT NOT NULL,
        imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        imported_by TEXT NOT NULL DEFAULT ''
      );
      CREATE TABLE IF NOT EXISTS guard_assignments(
        id INTEGER PRIMARY KEY,
        roster_date TEXT NOT NULL,
        sector TEXT NOT NULL CHECK(sector IN ('UMC','Réanimation chirurgicale')),
        raw_label TEXT NOT NULL,
        resident_id INTEGER REFERENCES residents(id) ON DELETE SET NULL,
        hours TEXT NOT NULL DEFAULT '16H-08H',
        mapping_status TEXT NOT NULL DEFAULT 'unresolved'
          CHECK(mapping_status IN ('unresolved','validated')),
        source_id INTEGER REFERENCES guard_sources(id) ON DELETE SET NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
      );
      CREATE INDEX IF NOT EXISTS idx_guard_date_sector
        ON guard_assignments(roster_date,sector);
      CREATE INDEX IF NOT EXISTS idx_guard_label
        ON guard_assignments(raw_label);
      CREATE TABLE IF NOT EXISTS guard_document_settings(
        month TEXT PRIMARY KEY,
        document_html TEXT NOT NULL DEFAULT '',
        signature_name TEXT NOT NULL DEFAULT '',
        signature_title TEXT NOT NULL DEFAULT '',
        updated_by TEXT NOT NULL DEFAULT '',
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
      );
    """)
    # Additive migration: removed residents stay in the audit trail instead of disappearing.
    columns = {row["name"] for row in c.execute("PRAGMA table_info(guard_assignments)").fetchall()}
    for name, spec in {
        "active": "INTEGER NOT NULL DEFAULT 1",
        "removed_reason": "TEXT NOT NULL DEFAULT ''",
        "removed_by": "TEXT NOT NULL DEFAULT ''",
        "removed_at": "TEXT NOT NULL DEFAULT ''",
    }.items():
        if name not in columns:
            c.execute(f"ALTER TABLE guard_assignments ADD COLUMN {name} {spec}")
    c.executescript("""
      CREATE TABLE IF NOT EXISTS guard_changes(
        id INTEGER PRIMARY KEY,
        roster_date TEXT NOT NULL,
        sector TEXT NOT NULL,
        change_type TEXT NOT NULL CHECK(change_type IN ('remove','replace')),
        assignment_id INTEGER,
        resident_label TEXT NOT NULL,
        reason TEXT NOT NULL,
        actor TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
      );
      CREATE INDEX IF NOT EXISTS idx_guard_changes_date
        ON guard_changes(roster_date,sector);
    """)
    existing = c.execute("SELECT id FROM guard_sources WHERE month='2026-10'").fetchone()
    if not existing and os.path.isfile(SOURCE_PATH):
        with open(SOURCE_PATH, "r", encoding="utf-8") as handle:
            source = json.load(handle)
        raw_json = json.dumps(source, ensure_ascii=False, separators=(",", ":"))
        digest = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()
        cur = c.execute(
            "INSERT INTO guard_sources(month,title,filename,source_sha256,raw_json,imported_by) VALUES(?,?,?,?,?,?)",
            (source["month"], source["title"], os.path.basename(SOURCE_PATH), digest, raw_json, "import ResiManage"),
        )
        source_id = cur.lastrowid
        imported = 0
        for day_index, (weekday, umc_names, surgical_name) in enumerate(source["days"], start=1):
            roster_date = date(2026, 10, day_index).isoformat()
            hours = "08H-08H" if weekday in ("VENDREDI", "SAMEDI") else "16H-08H"
            for sector, names in (("UMC", umc_names), ("Réanimation chirurgicale", surgical_name)):
                for raw_label in names.split("-"):
                    c.execute("""
                      INSERT INTO guard_assignments
                        (roster_date,sector,raw_label,hours,mapping_status,source_id)
                      VALUES(?,?,?,?, 'unresolved',?)
                    """, (roster_date, sector, raw_label.strip(), hours, source_id))
                    imported += 1
        audit_event(c, "guards.source_imported",
                    f"month=2026-10; assignments={imported}; source_sha256={digest}")
    c.commit()


def _safe_rich_html(value):
    """Keep only ReportLab-safe formatting tags and a small set of font attributes."""
    value = str(value or "")[:12000]
    value = re.sub(r"(?is)<(script|style|iframe|object)[^>]*>.*?</\\1>", "", value)
    value = re.sub(r"(?is)<!--.*?-->", "", value)
    value = re.sub(r"(?i)<(p|div)\\b[^>]*>", "", value)
    value = re.sub(r"(?i)</(p|div)\\s*>", "<br/>", value)
    value = re.sub(r"(?i)<br\\s*/?>", "<br/>", value)
    value = re.sub(r"(?i)<(?!/?(?:b|strong|i|em|u|font|br)\\b)[^>]*>", "", value)
    def clean_font(match):
        attrs = match.group(1) or ""
        safe = []
        color = re.search(r"(?i)\\bcolor\\s*=\\s*['\"]?(#[0-9a-f]{6}|#[0-9a-f]{3}|[a-z]{3,20})", attrs)
        face = re.search(r"(?i)\\bface\\s*=\\s*['\"]?([a-z0-9 ,_-]{1,40})", attrs)
        size = re.search(r"(?i)\\bsize\\s*=\\s*['\"]?([1-7])", attrs)
        if color: safe.append('color="' + color.group(1) + '"')
        if face:
            family = face.group(1).strip().lower()
            mapped = "Courier" if "courier" in family else "Times-Roman" if "times" in family or "georgia" in family else "Helvetica"
            safe.append('face="' + mapped + '"')
        if size: safe.append('size="' + size.group(1) + '"')
        return "<font " + " ".join(safe) + ">" if safe else "<font>"
    value = re.sub(r"(?i)<font\\b([^>]*)>", clean_font, value)
    value = re.sub(r"(?i)\\s+on[a-z]+\\s*=\\s*(['\"]).*?\\1", "", value)
    return value


def register_guard_routes(app, db, page, guard, audit_event, L):
    def prepare():
        c = db()
        _ensure_schema(c, audit_event)
        return c

    def month_redirect(value):
        return redirect("/guards?month=" + value)

    @app.route("/guards", methods=["GET", "POST"])
    def guards_calendar():
        denied = guard()
        if denied:
            return denied
        c = prepare()
        month = request.values.get("month", date.today().strftime("%Y-%m"))
        if not _valid_month(month):
            month = date.today().strftime("%Y-%m")
        if request.method == "POST":
            if session.get("role") != "super_admin":
                c.close()
                return ("Forbidden — Super Admin only", 403)
            action = request.form.get("action", "add")
            try:
                if action == "save_document":
                    document_html = _safe_rich_html(request.form.get("document_html", ""))
                    signature_name = request.form.get("signature_name", "").strip()[:120]
                    signature_title = request.form.get("signature_title", "").strip()[:160]
                    c.execute("""
                      INSERT INTO guard_document_settings(month,document_html,signature_name,signature_title,updated_by,updated_at)
                      VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)
                      ON CONFLICT(month) DO UPDATE SET document_html=excluded.document_html,
                        signature_name=excluded.signature_name,signature_title=excluded.signature_title,
                        updated_by=excluded.updated_by,updated_at=CURRENT_TIMESTAMP
                    """, (month, document_html, signature_name, signature_title, str(session.get("user", ""))))
                    audit_event(c, "guards.document_edited",
                                f"month={month}; signature={signature_name}")
                elif action == "move":
                    assignment_id = int(request.form.get("assignment_id", "0"))
                    target_date = request.form.get("target_date", "").strip()
                    target_sector = request.form.get("target_sector", "").strip()
                    target = date.fromisoformat(target_date)
                    if target.strftime("%Y-%m") != month or target_sector not in SECTORS:
                        raise ValueError("Destination invalide : choisissez une cellule du mois affiché.")
                    row = c.execute("SELECT * FROM guard_assignments WHERE id=? AND active=1", (assignment_id,)).fetchone()
                    if not row:
                        raise ValueError("Affectation introuvable ou inactive.")
                    duplicate = c.execute("""
                      SELECT 1 FROM guard_assignments
                      WHERE active=1 AND id<>? AND roster_date=? AND sector=?
                        AND ((resident_id IS NOT NULL AND resident_id=?) OR
                             (resident_id IS NULL AND raw_label=?))
                    """, (assignment_id, target_date, target_sector, row["resident_id"], row["raw_label"])).fetchone()
                    if duplicate:
                        raise ValueError("Ce résident figure déjà dans la cellule de destination.")
                    target_hours = "08H-08H" if target.weekday() in (4, 5) else "16H-08H"
                    c.execute("UPDATE guard_assignments SET roster_date=?,sector=?,hours=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                              (target_date, target_sector, target_hours, assignment_id))
                    audit_event(c, "guards.assignment_moved",
                                f"id={assignment_id}; from={row['roster_date']}|{row['sector']}; to={target_date}|{target_sector}")
                elif action == "swap":
                    assignment_id = int(request.form.get("assignment_id", "0"))
                    target_id = int(request.form.get("target_assignment_id", "0"))
                    if assignment_id == target_id:
                        raise ValueError("Choisissez deux résidents différents pour la permutation.")
                    first = c.execute("SELECT * FROM guard_assignments WHERE id=? AND active=1", (assignment_id,)).fetchone()
                    second = c.execute("SELECT * FROM guard_assignments WHERE id=? AND active=1", (target_id,)).fetchone()
                    if not first or not second:
                        raise ValueError("Une des deux affectations n’est plus active.")
                    if first["roster_date"][:7] != month or second["roster_date"][:7] != month:
                        raise ValueError("La permutation doit rester dans le mois affiché.")
                    c.execute("UPDATE guard_assignments SET roster_date=?,sector=?,hours=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                              (second["roster_date"], second["sector"], second["hours"], first["id"]))
                    c.execute("UPDATE guard_assignments SET roster_date=?,sector=?,hours=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
                              (first["roster_date"], first["sector"], first["hours"], second["id"]))
                    audit_event(c, "guards.assignments_swapped",
                                f"first={first['id']}:{first['roster_date']}|{first['sector']}; second={second['id']}:{second['roster_date']}|{second['sector']}")
                elif action == "delete":
                    assignment_id = int(request.form.get("assignment_id", "0"))
                    reason = request.form.get("reason", "").strip()
                    if len(reason) < 5:
                        raise ValueError("Indiquez un motif précis (au moins 5 caractères) pour retirer ce résident.")
                    row = c.execute(
                        "SELECT * FROM guard_assignments WHERE id=? AND active=1", (assignment_id,)
                    ).fetchone()
                    if not row:
                        raise ValueError("Affectation de garde introuvable ou déjà retirée.")
                    actor = str(session.get("user", ""))
                    c.execute("""
                      UPDATE guard_assignments
                      SET active=0,removed_reason=?,removed_by=?,removed_at=CURRENT_TIMESTAMP,
                          updated_at=CURRENT_TIMESTAMP
                      WHERE id=? AND active=1
                    """, (reason, actor, assignment_id))
                    c.execute("""
                      INSERT INTO guard_changes(roster_date,sector,change_type,assignment_id,resident_label,reason,actor)
                      VALUES(?,?,'remove',?,?,?,?)
                    """, (row["roster_date"], row["sector"], assignment_id, row["raw_label"], reason, actor))
                    audit_event(c, "guards.assignment_removed",
                                f"id={assignment_id}; date={row['roster_date']}; sector={row['sector']}; label={row['raw_label']}; reason={reason}")
                elif action == "add_many":
                    roster_date = request.form.get("roster_date", "").strip()
                    sector = request.form.get("sector", "").strip()
                    parsed = date.fromisoformat(roster_date)
                    if parsed.strftime("%Y-%m") != month:
                        raise ValueError("La date doit appartenir au mois affiché.")
                    if sector not in SECTORS:
                        raise ValueError("Service invalide.")
                    hours = "08H-08H" if parsed.weekday() in (4, 5) else "16H-08H"
                    selected_ids = list(dict.fromkeys(request.form.getlist("resident_ids")))
                    if not selected_ids:
                        raise ValueError("Sélectionnez au moins un résident.")
                    residents_to_add = []
                    for value in selected_ids:
                        resident_id = int(value)
                        resident = c.execute("""
                          SELECT r.id,r.surname,r.firstname,r.year FROM residents r
                          WHERE r.id=? AND r.status='active' AND r.year BETWEEN 1 AND 4
                            AND COALESCE(r.resident_type,'local')='local'
                            AND COALESCE(r.dems_status,'')<>'preparing'
                            AND NOT EXISTS(SELECT 1 FROM dems_archive d WHERE d.resident_id=r.id)
                        """, (resident_id,)).fetchone()
                        if not resident:
                            raise ValueError("Seuls les résidents locaux actifs des années 1 à 4 non dispensés pour préparation DEMS peuvent être sélectionnés.")
                        duplicate = c.execute("""
                          SELECT 1 FROM guard_assignments
                          WHERE active=1 AND roster_date=? AND sector=? AND resident_id=?
                        """, (roster_date, sector, resident_id)).fetchone()
                        if duplicate:
                            raise ValueError(f"{resident['surname']} {resident['firstname']} figure déjà dans ce service à cette date.")
                        residents_to_add.append(resident)
                    for resident in residents_to_add:
                        canonical = (resident["surname"] + " " + resident["firstname"]).strip()
                        c.execute("""
                          INSERT INTO guard_assignments(roster_date,sector,raw_label,resident_id,hours,mapping_status)
                          VALUES(?,?,?,?,?,'validated')
                        """, (roster_date, sector, canonical, resident["id"], hours))
                    audit_event(c, "guards.assignments_added",
                                f"date={roster_date}; sector={sector}; resident_ids={','.join(str(x['id']) for x in residents_to_add)}")
                elif action == "add":
                    roster_date = request.form.get("roster_date", "").strip()
                    sector = request.form.get("sector", "").strip()
                    hours = request.form.get("hours", "16H-08H").strip()
                    resident_value = request.form.get("resident_id", "").strip()
                    raw_label = request.form.get("raw_label", "").strip()
                    parsed = date.fromisoformat(roster_date)
                    if parsed.strftime("%Y-%m") != month:
                        raise ValueError("La date doit appartenir au mois affiché.")
                    if sector not in SECTORS or hours not in HOURS:
                        raise ValueError("Service ou horaire invalide.")
                    resident_id = None
                    status = "unresolved"
                    if resident_value:
                        resident_id = int(resident_value)
                        resident = c.execute("""
                          SELECT r.id,r.surname,r.firstname FROM residents r
                          WHERE r.id=? AND r.status='active' AND r.year BETWEEN 1 AND 4
                            AND COALESCE(r.resident_type,'local')='local'
                            AND COALESCE(r.dems_status,'')<>'preparing'
                            AND NOT EXISTS(SELECT 1 FROM dems_archive d WHERE d.resident_id=r.id)
                        """, (resident_id,)).fetchone()
                        if not resident:
                            raise ValueError("Seuls les résidents actifs des promotions 1 à 4 peuvent être affectés.")
                        canonical = (resident["surname"] + " " + resident["firstname"]).strip()
                        if raw_label and _normalise(raw_label) != _normalise(canonical):
                            raise ValueError("Le libellé doit correspondre au résident sélectionné.")
                        raw_label = canonical
                        status = "validated"
                    if not raw_label:
                        raise ValueError("Choisissez un résident ou saisissez un nom à identifier.")
                    duplicate = c.execute("""
                      SELECT 1 FROM guard_assignments
                      WHERE active=1 AND roster_date=? AND sector=? AND
                        ((? IS NOT NULL AND resident_id=?) OR raw_label=?)
                    """, (roster_date, sector, resident_id, resident_id, raw_label)).fetchone()
                    if duplicate:
                        raise ValueError("Cette personne figure déjà dans ce service à cette date.")
                    c.execute("""
                      INSERT INTO guard_assignments(roster_date,sector,raw_label,resident_id,hours,mapping_status)
                      VALUES(?,?,?,?,?,?)
                    """, (roster_date, sector, raw_label, resident_id, hours, status))
                    audit_event(c, "guards.assignment_added",
                                f"date={roster_date}; sector={sector}; label={raw_label}; resident_id={resident_id or ''}")
                else:
                    raise ValueError("Action inconnue.")
                c.commit()
                flash(L("Modification enregistrée.", "Change saved.", "تم حفظ التعديل."))
            except (ValueError, TypeError, OverflowError) as exc:
                c.rollback()
                flash(str(exc))
            except Exception:
                c.rollback()
                flash(L("Impossible d’enregistrer cette modification.", "Could not save this change.", "تعذر حفظ هذا التعديل."))
            c.close()
            return month_redirect(month)

        first_weekday, day_count = calendar.monthrange(*map(int, month.split("-")))
        assignments = c.execute("""
          SELECT g.*,r.surname,r.firstname,r.year
          FROM guard_assignments g
          LEFT JOIN residents r ON r.id=g.resident_id
          WHERE substr(g.roster_date,1,7)=? AND g.active=1
          ORDER BY g.roster_date,CASE g.sector WHEN 'UMC' THEN 0 ELSE 1 END,
                   COALESCE(r.surname,g.raw_label),COALESCE(r.firstname,'')
        """, (month,)).fetchall()
        by_day = {}
        for row in assignments:
            by_day.setdefault(row["roster_date"], {"UMC": [], "Réanimation chirurgicale": []})[row["sector"]].append(row)
        days = []
        for day_number in range(1, day_count + 1):
            d = date(int(month[:4]), int(month[5:]), day_number)
            iso = d.isoformat()
            days.append({
                "date": iso, "day": day_number, "weekday": WEEKDAYS[d.weekday()].capitalize(),
                "weekend": d.weekday() in (4, 5),
                "hours": "08H-08H" if d.weekday() in (4, 5) else "16H-08H",
                "umc": by_day.get(iso, {}).get("UMC", []),
                "surgical": by_day.get(iso, {}).get("Réanimation chirurgicale", []),
            })
        counts = {
            "total": len(assignments),
            "unresolved": sum(1 for row in assignments if row["mapping_status"] != "validated"),
            "validated": sum(1 for row in assignments if row["mapping_status"] == "validated"),
        }
        months = {row["month"] for row in c.execute("SELECT month FROM guard_sources").fetchall()}
        months.update(row[0] for row in c.execute("SELECT DISTINCT substr(roster_date,1,7) FROM guard_assignments").fetchall())
        months.add(date.today().strftime("%Y-%m"))
        months.add(month)
        month_options = [{"value": m, "label": _month_label(m)} for m in sorted(months, reverse=True)]
        residents = list(_eligible_residents(c))
        released_residents = list(_dems_preparation_residents(c))
        changes = c.execute("""
          SELECT * FROM guard_changes WHERE substr(roster_date,1,7)=?
          ORDER BY created_at DESC,id DESC
        """, (month,)).fetchall()
        source = c.execute("SELECT * FROM guard_sources WHERE month=?", (month,)).fetchone()
        document_settings = c.execute("SELECT * FROM guard_document_settings WHERE month=?", (month,)).fetchone()
        if not document_settings:
            document_settings = {"document_html": "", "signature_name": "", "signature_title": ""}
        c.close()
        return page("""<section class="rt-guards-hero">
          <div class="rt-guards-heading"><div><p class="rt-kicker">RESIMANAGE · PLANNING</p>
          <h1>🛡️ {{L('Gestion des gardes','Guard management','تسيير المناوبات')}}</h1>
          <p>{{L('Calendrier mensuel · UMC et Réanimation chirurgicale','Monthly calendar · Emergency and surgical intensive care','تقويم شهري · الاستعجالات والإنعاش الجراحي')}}</p></div>
          <div class="rt-guards-month"><form method="get"><label>{{L('Mois affiché','Displayed month','الشهر المعروض')}}</label><select name="month" onchange="this.form.submit()">{% for item in month_options %}<option value="{{item.value}}" {% if item.value==month %}selected{% endif %}>{{item.label}}</option>{% endfor %}</select></form></div></div>
          <div class="rt-guards-stats"><div><strong>{{counts.total}}</strong><span>{{L('Affectations','Assignments','التعيينات')}}</span></div><div><strong>{{counts.validated}}</strong><span>{{L('Identités validées','Validated identities','هويات مؤكدة')}}</span></div><div class="is-warning"><strong>{{counts.unresolved}}</strong><span>{{L('À identifier','To identify','تحتاج إلى تحديد')}}</span></div></div>
          {% if source_record %}<p class="rt-source-note">📚 {{L('Mois importé depuis le planning historique :','Month imported from historical roster:','شهر مستورد من جدول المناوبات التاريخي:')}} {{source_record.title}} · <a href="/guards/source/{{source_record.id}}">{{L('Voir la source','View source','عرض المصدر')}}</a></p>{% endif %}
          {% if month=='2026-10' %}<p class="rt-history-note">🔒 {{L('Planning historique importé. Les libellés d’origine sont conservés ; aucune identité n’a été attribuée automatiquement.','Historical roster imported. Original labels are preserved; no identity was assigned automatically.','تم استيراد الجدول التاريخي مع الحفاظ على التسميات الأصلية؛ لم يتم إسناد أي هوية تلقائيًا.')}}</p>{% elif counts.total==0 %}<p class="rt-draft-note">✎ {{L('Mois vierge : aucune garde n’a été générée. Ajoutez les affectations après validation du roulement.','Empty month: no shifts have been generated. Add assignments only after validating the rotation rules.','شهر فارغ: لم يتم إنشاء أي مناوبة. أضف التعيينات بعد التحقق من قواعد التناوب.')}}</p>{% endif %}
        </section>
        {% if role=='super_admin' %}<section class="rt-guard-editor"><h2>{{L('Règle de sélection','Selection rule','قاعدة الاختيار')}}</h2>
          <p>{{L('Chaque journée possède son propre sélecteur. Les résidents actifs des années 1 à 4 sont admissibles ; seuls ceux explicitement marqués en préparation DEMS sont dispensés.','Each day has its own selector. Active residents in years 1–4 are eligible; only those explicitly marked as preparing for DEMS are exempt.','لكل يوم قائمة اختيار خاصة. المقيمون النشطون من السنة 1 إلى 4 مؤهلون؛ ويُعفى فقط من تم تحديدهم صراحة للتحضير لـ DEMS.')}}</p></section>{% endif %}
        <section class="rt-guard-editor">
          <div class="rt-guard-editor-heading"><h2>📝 {{L('Mise en forme du document','Document formatting','تنسيق المستند')}}</h2><span>{{L('Outils de texte type Word','Word-style text tools','أدوات نص شبيهة بـ Word')}}</span></div>
          {% if role=='super_admin' %}
          <form method="post" id="rt-guard-document-form"><input type="hidden" name="month" value="{{month}}"><input type="hidden" name="action" value="save_document">
            <div class="rt-guard-toolbar" role="toolbar" aria-label="Mise en forme du texte">
              <button type="button" data-cmd="bold" title="Gras"><strong>G</strong></button><button type="button" data-cmd="italic" title="Italique"><em>I</em></button><button type="button" data-cmd="underline" title="Souligné"><u>U</u></button>
              <label>{{L('Taille','Size','الحجم')}} <select id="rt-guard-font-size"><option value="2">Petite</option><option value="3" selected>Normale</option><option value="4">Grande</option><option value="5">Très grande</option><option value="6">Titre</option><option value="7">Très grand titre</option></select></label>
              <label>{{L('Police','Font','الخط')}} <select id="rt-guard-font-family"><option>Arial</option><option>Georgia</option><option>Times New Roman</option><option>Courier New</option><option>Verdana</option></select></label>
              <label>{{L('Couleur','Color','اللون')}} <input id="rt-guard-font-color" type="color" value="#163b5c" aria-label="Couleur du texte"></label>
              <button type="button" data-cmd="removeFormat" title="Effacer la mise en forme">Tx</button>
            </div>
            <div id="rt-guard-rich-editor" class="rt-guard-rich-editor" contenteditable="true" role="textbox" aria-multiline="true" data-placeholder="{{L('Ajouter un titre, une note ou des consignes à la liste…','Add a title, note or instructions to the roster…','أضف عنوانًا أو ملاحظة أو تعليمات إلى القائمة…')}}">{{document_settings.document_html|safe}}</div>
            <textarea name="document_html" id="rt-guard-document-html" hidden></textarea>
            <div class="rt-guard-signature-fields"><label>{{L('Nom du signataire','Signatory name','اسم الموقّع')}}<input name="signature_name" value="{{document_settings.signature_name}}" maxlength="120" placeholder="{{L('Nom et prénom','Full name','الاسم واللقب')}}"></label><label>{{L('Fonction / qualité','Role / title','الصفة')}}<input name="signature_title" value="{{document_settings.signature_title}}" maxlength="160" placeholder="{{L('Chef de service, responsable…','Department head, supervisor…','رئيس المصلحة، المسؤول…')}}"></label><button type="submit">💾 {{L('Enregistrer le document','Save document','حفظ المستند')}}</button></div>
          </form>
          {% else %}{% if document_settings.document_html %}<div class="rt-guard-rich-preview">{{document_settings.document_html|safe}}</div>{% endif %}{% if document_settings.signature_name %}<p class="rt-guard-signature-preview">{{document_settings.signature_name}} · {{document_settings.signature_title}}</p>{% endif %}{% endif %}
        </section>
        <section class="rt-guard-calendar-section"><div class="rt-guard-calendar-title"><h2>{{month_label}}</h2><a class="button" href="/guards/mapping?month={{month}}">👤 {{L('Identifier les résidents','Identify residents','تحديد المقيمين')}}</a><a class="button" href="/guards/export.csv?month={{month}}">⬇ CSV</a><button type="button" onclick="window.print()">🖨 {{L('Imprimer','Print','طباعة')}}</button></div>
          <div class="wrap"><table class="rt-guard-calendar"><thead><tr><th>{{L('Jour','Day','اليوم')}}</th><th>{{L('UMC','Emergency','الاستعجالات')}}</th><th>{{L('Réanimation chirurgicale','Surgical ICU','الإنعاش الجراحي')}}</th></tr></thead><tbody>
          {% for day in days %}<tr class="{% if day.weekend %}rt-weekend{% endif %}"><th><strong>{{day.day}}</strong><span>{{day.weekday}}</span><small>{{day.date[8:10]}}/{{day.date[5:7]}}/{{day.date[:4]}}</small></th>
            {% for sector,items in [('UMC',day.umc),('Réanimation chirurgicale',day.surgical)] %}<td><div class="rt-guard-cell" data-guard-drop-cell data-date="{{day.date}}" data-sector="{{sector}}"><div class="rt-guard-hours">{{items[0].hours if items else day.hours}}</div>
              {% for item in items %}<div class="rt-guard-person {% if item.mapping_status!='validated' %}is-unresolved{% endif %}" data-guard-chip data-assignment-id="{{item.id}}" data-rid="{{item.resident_id or ''}}" draggable="true"><span class="{% if item.resident_id %}rt-guard-profile-link{% endif %}" {% if item.resident_id %}data-guard-profile="{{item.resident_id}}" role="button" tabindex="0"{% endif %}>{{(item.surname~' '~item.firstname) if item.resident_id else item.raw_label}}</span>{% if item.resident_id %}<small>{{item.year}}{{L('e année','th year',' سنة')}}</small>{% else %}<small>{{L('À identifier','Unresolved','غير محدد')}}</small>{% endif %}
                {% if role=='super_admin' %}<details class="rt-guard-remove"><summary title="{{L('Corriger cette affectation','Correct this assignment','تصحيح هذا التعيين')}}">×</summary><form method="post"><input type="hidden" name="month" value="{{month}}"><input type="hidden" name="action" value="delete"><input type="hidden" name="assignment_id" value="{{item.id}}"><input name="reason" required minlength="5" maxlength="300" placeholder="{{L('Motif obligatoire du retrait','Required reason for removal','سبب الإزالة إلزامي')}}" aria-label="{{L('Motif du retrait','Removal reason','سبب الإزالة')}}"><button type="submit">{{L('Confirmer','Confirm','تأكيد')}}</button></form></details>{% endif %}</div>{% endfor %}
              {% if not items %}<span class="rt-guard-empty">{{L('Aucune affectation','No assignment','لا يوجد تعيين')}}</span>{% endif %}
              {% if role=='super_admin' %}<form method="post" class="rt-guard-day-selector"><input type="hidden" name="month" value="{{month}}"><input type="hidden" name="action" value="add_many"><input type="hidden" name="roster_date" value="{{day.date}}"><input type="hidden" name="sector" value="{{sector}}"><label>{{L('Ajouter des résidents','Add residents','إضافة مقيمين')}}<select name="resident_ids" multiple size="1" required aria-label="{{L('Sélectionner les résidents de cette journée','Select residents for this day','اختيار مقيمي هذا اليوم')}}">{% for r in residents %}<option value="{{r.id}}">{{r.surname}} {{r.firstname}} · {{r.year}}{{L('e année','th year',' سنة')}}</option>{% endfor %}{% for r in released_residents %}<option value="" disabled>{{r.surname}} {{r.firstname}} · 4{{L('e année · dispensé DEMS','th year · DEMS leave',' سنة · إعفاء DEMS')}}</option>{% endfor %}</select></label><button type="submit">＋ {{L('Ajouter la sélection','Add selection','إضافة المحددين')}}</button></form>{% endif %}</div></td>{% endfor %}
          </tr>{% endfor %}</tbody></table></div>
          <p class="rt-guard-footnote">{{L('Les gardes du vendredi et du samedi sont affichées en 08H–08H ; les autres jours en 16H–08H, conformément au planning d’octobre 2026. Vérifiez l’horaire avant toute nouvelle saisie.','Friday and Saturday shifts are shown as 08H-08H; other days as 16H-08H, matching the October 2026 source.','مناوبات الجمعة والسبت من 08 إلى 08؛ وبقية الأيام من 16 إلى 08، وفق جدول أكتوبر 2026.')}}</p>
          <p><a class="button" href="/guards/export.pdf?month={{month}}">⬇ {{L('Télécharger le PDF','Download PDF','تنزيل PDF')}}</a></p>
        </section>
        {% if changes %}<section class="rt-guard-changes"><h2>{{L('Historique des correctifs','Correction history','سجل التصحيحات')}}</h2><div class="wrap"><table><tr><th>{{L('Date','Date','التاريخ')}}</th><th>{{L('Service','Sector','القسم')}}</th><th>{{L('Résident retiré','Removed resident','المقيم المحذوف')}}</th><th>{{L('Motif','Reason','السبب')}}</th><th>{{L('Auteur','By','بواسطة')}}</th><th>{{L('Horodatage','Timestamp','الوقت')}}</th></tr>{% for change in changes %}<tr><td>{{change.roster_date}}</td><td>{{change.sector}}</td><td>{{change.resident_label}}</td><td>{{change.reason}}</td><td>{{change.actor}}</td><td>{{change.created_at}}</td></tr>{% endfor %}</table></div></section>{% endif %}
        <div class="rt-guard-profile-backdrop" id="rt-guard-profile-modal" hidden><section class="rt-guard-profile-dialog" role="dialog" aria-modal="true" aria-label="Fiche résident"><button type="button" id="rt-guard-profile-close" aria-label="Fermer">×</button><div id="rt-guard-profile-content"></div></section></div>
        <script>
        (function(){
          var editor=document.getElementById('rt-guard-rich-editor'),form=document.getElementById('rt-guard-document-form');
          if(editor&&form){
            form.addEventListener('submit',function(){document.getElementById('rt-guard-document-html').value=editor.innerHTML;});
            document.querySelectorAll('.rt-guard-toolbar [data-cmd]').forEach(function(button){button.addEventListener('click',function(){editor.focus();document.execCommand(button.dataset.cmd,false,null);});});
            var size=document.getElementById('rt-guard-font-size'),family=document.getElementById('rt-guard-font-family'),color=document.getElementById('rt-guard-font-color');
            size.addEventListener('change',function(){editor.focus();document.execCommand('fontSize',false,size.value);});
            family.addEventListener('change',function(){editor.focus();document.execCommand('fontName',false,family.value);});
            color.addEventListener('input',function(){editor.focus();document.execCommand('foreColor',false,color.value);});
          }
          var modal=document.getElementById('rt-guard-profile-modal'),profileContent=document.getElementById('rt-guard-profile-content');
          function addLine(parent,label,value){if(value===null||value===undefined||String(value).trim()==='')return;var p=document.createElement('p'),b=document.createElement('strong');b.textContent=label+': ';p.appendChild(b);p.appendChild(document.createTextNode(String(value)));parent.appendChild(p);}
          function openProfile(id){modal.hidden=false;profileContent.textContent='Chargement…';fetch('/api/residents/'+encodeURIComponent(id)+'/profile',{credentials:'same-origin',headers:{Accept:'application/json'}}).then(function(r){if(!r.ok)throw new Error('Fiche indisponible');return r.json();}).then(function(data){profileContent.textContent='';var r=data.resident||{},h=document.createElement('h2');h.textContent=((r.surname||'')+' '+(r.firstname||'')).trim();profileContent.appendChild(h);addLine(profileContent,'Année','A'+(r.year||'—'));addLine(profileContent,'Statut',r.status);addLine(profileContent,'Téléphone',r.phone);addLine(profileContent,'E-mail',r.email);addLine(profileContent,'Adresse',r.address);var title=document.createElement('h3');title.textContent='Historique des stages';profileContent.appendChild(title);(data.history||[]).forEach(function(item){addLine(profileContent,(item.year_label||'')+' · '+(item.period||''),item.terrain+' · '+(item.start_date||'')+' → '+(item.end_date||''));});}).catch(function(e){profileContent.textContent=e.message;});}
          document.querySelectorAll('[data-guard-profile]').forEach(function(el){el.addEventListener('click',function(){openProfile(el.dataset.guardProfile);});el.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();openProfile(el.dataset.guardProfile);}});});
          document.getElementById('rt-guard-profile-close').addEventListener('click',function(){modal.hidden=true;});
          modal.addEventListener('click',function(e){if(e.target===modal)modal.hidden=true;});
          var dragged=null,longTimer=null,longActive=false;
          function submitMove(id,cell){var data=new FormData();data.set('month','{{month}}');data.set('action','move');data.set('assignment_id',id);data.set('target_date',cell.dataset.date);data.set('target_sector',cell.dataset.sector);post(data);}
          function submitSwap(id,target){var data=new FormData();data.set('month','{{month}}');data.set('action','swap');data.set('assignment_id',id);data.set('target_assignment_id',target);post(data);}
          function post(data){var form=document.createElement('form');form.method='post';form.action='/guards?month={{month}}';data.forEach(function(v,k){var input=document.createElement('input');input.type='hidden';input.name=k;input.value=v;form.appendChild(input);});document.body.appendChild(form);form.submit();}
          document.querySelectorAll('[data-guard-chip]').forEach(function(chip){
            chip.addEventListener('dragstart',function(e){dragged=chip; e.dataTransfer.setData('text/plain',chip.dataset.assignmentId);e.dataTransfer.effectAllowed='move';});
            chip.addEventListener('dragend',function(){dragged=null;});
            chip.addEventListener('pointerdown',function(e){if(e.pointerType==='mouse')return;longActive=false;longTimer=window.setTimeout(function(){longActive=true;dragged=chip;chip.classList.add('is-dragging');},420);});
            chip.addEventListener('pointermove',function(e){if(longActive){e.preventDefault();chip.style.setProperty('--drag-x',e.clientX+'px');chip.style.setProperty('--drag-y',e.clientY+'px');}});
            chip.addEventListener('pointerup',function(e){window.clearTimeout(longTimer);if(!longActive)return;var target=document.elementFromPoint(e.clientX,e.clientY),other=target&&target.closest('[data-guard-chip]'),cell=target&&target.closest('[data-guard-drop-cell]');chip.classList.remove('is-dragging');if(other&&other!==chip)submitSwap(chip.dataset.assignmentId,other.dataset.assignmentId);else if(cell)submitMove(chip.dataset.assignmentId,cell);dragged=null;longActive=false;});
            chip.addEventListener('pointercancel',function(){window.clearTimeout(longTimer);chip.classList.remove('is-dragging');dragged=null;longActive=false;});
          });
          document.querySelectorAll('[data-guard-drop-cell]').forEach(function(cell){
            cell.addEventListener('dragover',function(e){e.preventDefault();cell.classList.add('is-drop-target');});
            cell.addEventListener('dragleave',function(){cell.classList.remove('is-drop-target');});
            cell.addEventListener('drop',function(e){e.preventDefault();cell.classList.remove('is-drop-target');var target=e.target.closest('[data-guard-chip]');var id=e.dataTransfer.getData('text/plain');if(!id||!dragged)return;if(target&&target.dataset.assignmentId!==id)submitSwap(id,target.dataset.assignmentId);else submitMove(id,cell);});
          });
        })();
        </script>
        <style>
        .rt-guards-hero{background:linear-gradient(130deg,#092b50,#135b83 58%,#126c70)!important;color:#effaff!important;border:1px solid #65d8ef!important}
        .rt-guard-editor{border:1px solid #70b5d3!important;background:linear-gradient(145deg,#0c2b49,#132c4d)!important;color:#eefaff!important}
        .rt-guard-editor h2,.rt-guard-editor label{color:#eefaff!important}
        .rt-guard-editor-heading{display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap}
        .rt-guard-toolbar{display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:8px;background:#061a2d;border:1px solid #4b819d;border-radius:10px}
        .rt-guard-toolbar button{min-width:34px;min-height:34px;padding:5px 9px;background:#174c70!important;color:#fff!important;border:1px solid #75b8d8!important;border-radius:7px}
        .rt-guard-toolbar label{display:flex;align-items:center;gap:5px;font-size:11px;font-weight:800}
        .rt-guard-toolbar select{min-height:32px;background:#fff!important;color:#16334b!important}
        .rt-guard-toolbar input[type=color]{width:38px;height:32px;padding:2px}
        .rt-guard-rich-editor,.rt-guard-rich-preview{min-height:82px;margin-top:9px;padding:12px;background:#fff;color:#172b3c;border:1px solid #8fb6c9;border-radius:9px;outline:none}
        .rt-guard-rich-editor:empty:before{content:attr(data-placeholder);color:#738696}
        .rt-guard-signature-fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:10px;align-items:end}
        .rt-guard-signature-fields button{grid-column:1/-1}
        .rt-guard-signature-preview{text-align:end;font-weight:800}
        .rt-guard-profile-backdrop{position:fixed;inset:0;z-index:5000;display:grid;place-items:center;padding:14px;background:#020b16c9}
        .rt-guard-profile-backdrop[hidden]{display:none}
        .rt-guard-profile-dialog{width:min(720px,96vw);max-height:88vh;overflow:auto;padding:20px;background:#f7fbff;color:#17334b;border-radius:18px;box-shadow:0 22px 70px #0009}
        .rt-guard-profile-dialog>button{float:right;font-size:24px;background:#8c2d42!important;color:#fff!important}
        .rt-guard-profile-link{cursor:pointer;text-decoration:underline;text-decoration-color:#85d8f4;text-underline-offset:3px}
        .rt-guard-person{touch-action:pan-y;cursor:grab}
        .rt-guard-person.is-dragging{opacity:.5;outline:3px dashed #5de2ed}
        .rt-guard-cell.is-drop-target{outline:3px solid #36d7c4;outline-offset:-3px;background:#15516a}
        @media(max-width:680px){.rt-guard-signature-fields{grid-template-columns:1fr}.rt-guard-toolbar{position:sticky;top:0;z-index:3}}
        .rt-guards-hero h1,.rt-guards-hero p,.rt-guards-hero label{color:#effaff!important}
        .rt-guards-heading{display:flex;justify-content:space-between;gap:14px;align-items:center;flex-wrap:wrap}.rt-kicker{font-size:11px;letter-spacing:.16em;font-weight:900;opacity:.8}
        .rt-guards-month{min-width:190px;max-width:260px}.rt-guards-month select{background:#061d35!important;color:#fff!important}
        .rt-guards-stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin-top:16px}
        .rt-guards-stats>div{display:flex;flex-direction:column;padding:12px;border-radius:13px;background:#ffffff18;border:1px solid #ffffff35}
        .rt-guards-stats strong{font-size:25px;color:#fff}.rt-guards-stats span{font-size:12px;color:#d9f4ff}.rt-guards-stats .is-warning{background:#7b3b1e66;border-color:#ffbf7c}
        .rt-history-note,.rt-draft-note,.rt-source-note{padding:10px 12px;border-radius:10px;background:#ffffff18;color:#fff!important}
        .rt-guard-add-form{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 12px;align-items:end}.rt-guard-add-form button{grid-column:1/-1}
        .rt-guard-calendar-title{display:flex;align-items:center;gap:8px;flex-wrap:wrap;justify-content:space-between}.rt-guard-calendar-title h2{margin-inline-end:auto}
        .rt-guard-calendar{min-width:760px;border-collapse:separate;border-spacing:0}.rt-guard-calendar th,.rt-guard-calendar td{vertical-align:top;padding:9px;border:1px solid #ffffff22}
        .rt-guard-calendar thead th{position:sticky;top:0;background:#0a3659!important;color:#fff!important}
        .rt-guard-calendar tbody th{min-width:92px;background:#102f4d!important;color:#fff!important}.rt-guard-calendar tbody th strong{display:block;font-size:21px}.rt-guard-calendar tbody th span,.rt-guard-calendar tbody th small{display:block;color:#c7e8f7!important}
        .rt-guard-calendar tbody tr.rt-weekend th{background:#563c67!important}.rt-guard-cell{min-width:250px;display:grid;gap:5px}
        .rt-guard-hours{font-size:11px;font-weight:900;color:#8deaff}.rt-guard-person{display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:6px 7px;border:1px solid #2c967d;background:#0d493e;border-radius:8px;color:#f1fffa}
        .rt-guard-person.is-unresolved{background:#563b20;border-color:#d48d42}.rt-guard-person span{font-weight:750}.rt-guard-person small{font-size:10px;color:#d8eee9}.rt-guard-person form{margin-inline-start:auto}.rt-guard-person button{padding:0 7px;min-height:24px;background:#7f2734!important;border-radius:6px}
        .rt-guard-empty{color:#a9bdca;font-size:12px;font-style:italic}.rt-guard-footnote{font-size:12px;color:#a9bdca}
        .rt-guard-day-selector{display:grid;gap:6px;margin-top:10px;padding:9px;border:1px solid #4e9bb7;border-radius:11px;background:#06243b}
        .rt-guard-day-selector label{display:grid;gap:5px;color:#c9f5ff;font-size:11px;font-weight:800}
        .rt-guard-day-selector select{width:100%;min-width:0;background:#f5fbff;color:#17334b;border:1px solid #74c9df;border-radius:8px;padding:7px;min-height:110px}
        .rt-guard-day-selector option:disabled{color:#8b9299;background:#e4e7eb}
        .rt-guard-day-selector button{width:100%;min-height:38px;border:1px solid #7de8d1;border-radius:9px;background:linear-gradient(145deg,#147c79,#0c4b65);color:#fff;font-weight:900;box-shadow:0 5px 0 #062d43,0 9px 16px #0006;transition:transform .12s,box-shadow .12s}
        .rt-guard-day-selector button:active{transform:translateY(4px);box-shadow:0 1px 0 #062d43,0 3px 7px #0006}
        .rt-guard-remove{margin-inline-start:auto}.rt-guard-remove summary{cursor:pointer;list-style:none;padding:2px 8px;border-radius:6px;background:#812c3c;color:#fff;font-weight:900}
        .rt-guard-remove form{display:grid;gap:4px;min-width:180px;padding:7px;background:#2c1720;border:1px solid #b95b6b;border-radius:8px}
        .rt-guard-remove input{min-width:0;width:100%;font-size:11px;padding:6px}
        .rt-guard-remove button{background:#9d273a!important;color:white;border-radius:7px;padding:5px}
        .rt-guard-changes{border-color:#9b6336!important}

        @media(max-width:680px){.rt-guard-add-form{grid-template-columns:1fr}.rt-guard-add-form button{grid-column:1}.rt-guards-stats strong{font-size:21px}.rt-guards-stats span{font-size:10px}.rt-guard-calendar-title{align-items:stretch}.rt-guard-calendar-title a{flex:1;text-align:center}}
        @media print{body{background:#fff!important;color:#111!important}header,.main-nav,.rt-back-link,.rt-footer,.rt-guards-hero,.rt-guard-editor,.rt-guard-calendar-title>a,.rt-guard-calendar-title>button,.rt-guard-person form{display:none!important}.rt-app-shell{display:block!important;padding:0!important}main{max-width:none!important;padding:0!important}section{margin:0!important;padding:0!important;border:0!important;box-shadow:none!important;background:#fff!important}.rt-guard-calendar{min-width:0!important;font-size:9px!important}.rt-guard-calendar th,.rt-guard-calendar td{color:#111!important;background:#fff!important;border:1px solid #555!important}.rt-guard-person{background:#fff!important;color:#111!important;border:1px solid #555!important}.rt-guard-person small,.rt-guard-hours{color:#333!important}.rt-guard-calendar tbody th span,.rt-guard-calendar tbody th small{color:#333!important}}
        </style>""", month=month, month_label=_month_label(month), month_options=month_options,
                    days=days, counts=counts, source_record=source, residents=residents, released_residents=released_residents, changes=changes, document_settings=document_settings)

    @app.route("/guards/mapping", methods=["GET", "POST"])
    def guards_mapping():
        denied = guard()
        if denied:
            return denied
        c = prepare()
        if session.get("role") != "super_admin":
            c.close()
            return ("Forbidden — Super Admin only", 403)
        month = request.args.get("month", date.today().strftime("%Y-%m"))
        if not _valid_month(month):
            month = date.today().strftime("%Y-%m")
        if request.method == "POST":
            raw_label = request.form.get("raw_label", "").strip()
            resident_value = request.form.get("resident_id", "").strip()
            try:
                if not raw_label:
                    raise ValueError("Libellé manquant.")
                resident_id = int(resident_value) if resident_value else None
                if resident_id is not None:
                    eligible = c.execute("""
                      SELECT r.id,r.surname,r.firstname FROM residents r
                      WHERE r.id=? AND r.status='active' AND r.year BETWEEN 1 AND 4
                        AND COALESCE(r.resident_type,'local')='local'
                        AND COALESCE(r.dems_status,'')<>'preparing'
                        AND NOT EXISTS(SELECT 1 FROM dems_archive d WHERE d.resident_id=r.id)
                    """, (resident_id,)).fetchone()
                    if not eligible:
                        raise ValueError("Résident non admissible : promotions actives 1 à 4 uniquement.")
                status = "validated" if resident_id is not None else "unresolved"
                c.execute("""
                  UPDATE guard_assignments SET resident_id=?,mapping_status=?,updated_at=CURRENT_TIMESTAMP
                  WHERE raw_label=?
                """, (resident_id, status, raw_label))
                changed = c.execute("SELECT changes()").fetchone()[0]
                audit_event(c, "guards.identity_mapped",
                            f"raw_label={raw_label}; resident_id={resident_id or ''}; assignments_updated={changed}")
                c.commit()
                flash(L("Correspondance enregistrée pour toutes les occurrences de ce libellé.",
                        "Mapping saved for every occurrence of this label.",
                        "تم حفظ المطابقة لكل مرات ظهور هذه التسمية."))
            except (ValueError, TypeError) as exc:
                c.rollback()
                flash(str(exc))
            c.close()
            return redirect("/guards/mapping?month=" + month)
        residents = _eligible_residents(c)
        labels = c.execute("""
          SELECT raw_label,COUNT(*) AS occurrences,
                 SUM(CASE WHEN mapping_status='validated' THEN 1 ELSE 0 END) AS validated_count,
                 MAX(resident_id) AS resident_id
          FROM guard_assignments
          WHERE substr(roster_date,1,7)=?
          GROUP BY raw_label ORDER BY mapping_status,raw_label COLLATE NOCASE
        """, (month,)).fetchall()
        resident_by_id = {r["id"]: r for r in residents}
        suggestions = {}
        by_surname = {}
        for r in residents:
            by_surname.setdefault(_normalise(r["surname"]), []).append(r)
        for item in labels:
            candidates = by_surname.get(_normalise(item["raw_label"]), [])
            suggestions[item["raw_label"]] = candidates[0] if len(candidates) == 1 else None
        c.close()
        return page("""<section><p class="rt-kicker">RESIMANAGE · CONTRÔLE DES IDENTITÉS</p>
          <h1>👤 {{L('Correspondance des noms','Name matching','مطابقة الأسماء')}}</h1>
          <p>{{L('Chaque libellé historique doit être relié manuellement à un résident. Une suggestion exacte peut être affichée, mais elle n’est jamais validée automatiquement. Les initiales ambiguës restent à vérifier.','Every historical label must be linked manually to a resident. An exact suggestion may be shown, but it is never accepted automatically. Ambiguous initials remain unresolved.','يجب ربط كل تسمية تاريخية يدويًا بمقيم. قد يظهر اقتراح مطابق تمامًا لكنه لا يعتمد تلقائيًا. تبقى الأحرف الأولى الملتبسة بحاجة إلى التحقق.')}}</p>
          <p><a class="button" href="/guards?month={{month}}">← {{L('Retour au calendrier','Back to calendar','العودة إلى التقويم')}}</a></p></section>
          <section><h2>{{L('Libellés du mois','Labels in this month','تسميات هذا الشهر')}} · {{month}}</h2><div class="wrap"><table><tr><th>{{L('Libellé source','Source label','التسمية الأصلية')}}</th><th>{{L('Occurrences','Occurrences','التكرارات')}}</th><th>{{L('Suggestion exacte (non validée)','Exact suggestion (not validated)','اقتراح مطابق (غير معتمد)')}}</th><th>{{L('Résident à confirmer','Resident to confirm','المقيم للتأكيد')}}</th><th>{{L('Statut','Status','الحالة')}}</th></tr>
          {% for item in labels %}<tr><td><strong>{{item.raw_label}}</strong></td><td>{{item.occurrences}}</td><td>{% if suggestions[item.raw_label] %}{{suggestions[item.raw_label].surname}} {{suggestions[item.raw_label].firstname}} · {{suggestions[item.raw_label].year}}{{L('e année','th year',' سنة')}}{% else %}—{% endif %}</td>
          <td><form method="post" class="rt-map-form"><input type="hidden" name="raw_label" value="{{item.raw_label}}"><select name="resident_id"><option value="">{{L('Laisser non identifié','Leave unresolved','اتركه دون تحديد')}}</option>{% for r in residents %}<option value="{{r.id}}" {% if item.resident_id==r.id %}selected{% endif %}>{{r.surname}} {{r.firstname}} · {{r.year}}{{L('e année','th year',' سنة')}}</option>{% endfor %}</select><button type="submit">{{L('Valider','Validate','تأكيد')}}</button></form></td>
          <td>{% if item.validated_count==item.occurrences %}<span class="rt-map-ok">{{L('Validé','Validated','مؤكد')}}</span>{% else %}<span class="rt-map-pending">{{L('À vérifier','Review','للمراجعة')}}</span>{% endif %}</td></tr>{% endfor %}</table></div>
          <p class="muted">{{L('La validation met à jour toutes les dates où ce libellé apparaît. Les libellés d’origine restent conservés dans l’historique.','Validation updates every date on which this label appears. Original labels remain preserved in the history.','يؤدي التأكيد إلى تحديث جميع التواريخ التي تظهر فيها التسمية. تبقى التسميات الأصلية محفوظة في السجل.')}}</p></section>
          <style>.rt-map-form{display:flex;gap:6px;align-items:center;min-width:280px}.rt-map-form select{min-width:150px}.rt-map-ok{color:#36d6a5;font-weight:800}.rt-map-pending{color:#ffb66b;font-weight:800}@media(max-width:680px){.rt-map-form{display:grid;min-width:160px}.rt-map-form button{width:100%}}</style>""",
                    month=month, labels=labels, residents=residents, suggestions=suggestions)

    @app.get("/guards/export.pdf")
    def guards_export_pdf():
        denied = guard()
        if denied:
            return denied
        c = prepare()
        month = request.args.get("month", date.today().strftime("%Y-%m"))
        if not _valid_month(month):
            c.close()
            return ("Invalid month", 400)
        rows = c.execute("""
          SELECT g.roster_date,g.sector,g.raw_label,g.hours,r.surname,r.firstname,r.year
          FROM guard_assignments g LEFT JOIN residents r ON r.id=g.resident_id
          WHERE substr(g.roster_date,1,7)=? AND g.active=1
          ORDER BY g.roster_date,CASE g.sector WHEN 'UMC' THEN 0 ELSE 1 END,
                   COALESCE(r.surname,g.raw_label),COALESCE(r.firstname,'')
        """, (month,)).fetchall()
        changes = c.execute("""
          SELECT roster_date,sector,resident_label,reason,actor,created_at
          FROM guard_changes WHERE substr(roster_date,1,7)=?
          ORDER BY created_at,id
        """, (month,)).fetchall()
        document_settings = c.execute("SELECT * FROM guard_document_settings WHERE month=?", (month,)).fetchone()
        c.close()
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from xml.sax.saxutils import escape

        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=landscape(A4),
                                rightMargin=10*mm,leftMargin=10*mm,
                                topMargin=10*mm,bottomMargin=10*mm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("GuardTitle", parent=styles["Title"], alignment=TA_CENTER,
                                     textColor=colors.HexColor("#123b5a"), fontSize=16, leading=20)
        small_style = ParagraphStyle("GuardSmall", parent=styles["BodyText"], fontSize=7, leading=9)
        heading_style = ParagraphStyle("GuardHeading", parent=styles["Heading2"], fontSize=10, leading=12)
        grouped = {}
        for row in rows:
            grouped.setdefault(row["roster_date"], {"UMC": [], "Réanimation chirurgicale": [], "hours": row["hours"]})
            name = ((row["surname"] or "") + " " + (row["firstname"] or "")).strip() or row["raw_label"]
            grouped[row["roster_date"]][row["sector"]].append(name)
        year, month_number = map(int, month.split("-"))
        _, day_count = calendar.monthrange(year, month_number)
        story = [Paragraph("LISTE DE GARDE DES RÉSIDENTS — " + escape(_month_label(month).upper()), title_style),
                 Spacer(1, 5*mm)]
        if document_settings and document_settings["document_html"]:
            story += [Paragraph(_safe_rich_html(document_settings["document_html"]), styles["BodyText"]), Spacer(1, 3*mm)]
        data = [[Paragraph("<b>DATE</b>", small_style), Paragraph("<b>HORAIRES</b>", small_style),
                 Paragraph("<b>UMC</b>", small_style), Paragraph("<b>RÉANIMATION CHIRURGICALE</b>", small_style)]]
        for day_number in range(1, day_count + 1):
            d = date(year, month_number, day_number)
            item = grouped.get(d.isoformat(), {"UMC": [], "Réanimation chirurgicale": [],
                                                "hours": "08H-08H" if d.weekday() in (4,5) else "16H-08H"})
            date_label = d.strftime("%d/%m/%Y") + " · " + WEEKDAYS[d.weekday()].capitalize()
            data.append([Paragraph(escape(date_label), small_style),
                         Paragraph(escape(item["hours"]), small_style),
                         Paragraph("<br/>".join(escape(x) for x in item["UMC"]) or "—", small_style),
                         Paragraph("<br/>".join(escape(x) for x in item["Réanimation chirurgicale"]) or "—", small_style)])
        table = Table(data, colWidths=[42*mm,25*mm,95*mm,95*mm], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#123b5a")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#8da3b5")),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#edf4f8")]),
            ("LEFTPADDING",(0,0),(-1,-1),5),("RIGHTPADDING",(0,0),(-1,-1),5),
            ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
        ]))
        story.append(table)
        if document_settings and (document_settings["signature_name"] or document_settings["signature_title"]):
            story += [Spacer(1, 12*mm), Paragraph("Signature et cachet", heading_style),
                      Paragraph(escape(document_settings["signature_name"]) + (" — " + escape(document_settings["signature_title"]) if document_settings["signature_title"] else ""), small_style),
                      Spacer(1, 14*mm), Paragraph("Signature : __________________________________________", small_style)]
        if changes:
            story += [Spacer(1,5*mm),Paragraph("HISTORIQUE DES CORRECTIFS",heading_style)]
            change_data = [[Paragraph("<b>Date</b>",small_style),Paragraph("<b>Secteur</b>",small_style),
                            Paragraph("<b>Résident retiré</b>",small_style),Paragraph("<b>Motif</b>",small_style),
                            Paragraph("<b>Auteur</b>",small_style),Paragraph("<b>Date du correctif</b>",small_style)]]
            for change in changes:
                change_data.append([Paragraph(escape(change["roster_date"]),small_style),
                                    Paragraph(escape(change["sector"]),small_style),
                                    Paragraph(escape(change["resident_label"]),small_style),
                                    Paragraph(escape(change["reason"]),small_style),
                                    Paragraph(escape(change["actor"]),small_style),
                                    Paragraph(escape(change["created_at"]),small_style)])
            correction_table=Table(change_data,colWidths=[28*mm,38*mm,42*mm,82*mm,30*mm,37*mm],repeatRows=1)
            correction_table.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#7f2938")),
                ("TEXTCOLOR",(0,0),(-1,0),colors.white),
                ("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#a58c90")),
                ("VALIGN",(0,0),(-1,-1),"TOP"),("FONTSIZE",(0,0),(-1,-1),7),
            ]))
            story.append(correction_table)
        doc.build(story)
        output.seek(0)
        return send_file(output,mimetype="application/pdf",as_attachment=True,
                         download_name=f"gardes_{month}.pdf")

    @app.get("/guards/source/<int:source_id>")
    def guards_source(source_id):
        denied = guard()
        if denied:
            return denied
        c = prepare()
        source = c.execute("SELECT * FROM guard_sources WHERE id=?", (source_id,)).fetchone()
        if not source:
            c.close()
            return ("Source not found", 404)
        c.close()
        return page("""<section><h1>📚 {{L('Source historique','Historical source','المصدر التاريخي')}}</h1>
          <h2>{{source_record.title}}</h2><p>{{L('Fichier','File','الملف')}} : {{source_record.filename}}</p>
          <p>{{L('Importé le','Imported on','تاريخ الاستيراد')}} : {{source_record.imported_at}}</p>
          <p>{{L('Empreinte SHA-256','SHA-256 fingerprint','بصمة SHA-256')}} : <code>{{source_record.source_sha256}}</code></p>
          <p>{{L('Les données importées sont conservées séparément des modifications du calendrier.','Imported data is preserved separately from calendar edits.','يتم الاحتفاظ بالبيانات المستوردة بشكل منفصل عن تعديلات التقويم.')}}</p>
          <a class="button" href="/guards?month={{source_record.month}}">← {{L('Retour','Back','عودة')}}</a></section>""", source_record=source)

    @app.get("/guards/export.csv")
    def guards_export():
        denied = guard()
        if denied:
            return denied
        c = prepare()
        month = request.args.get("month", date.today().strftime("%Y-%m"))
        if not _valid_month(month):
            c.close()
            return ("Invalid month", 400)
        rows = c.execute("""
          SELECT g.roster_date,g.sector,g.raw_label,g.hours,g.mapping_status,
                 r.surname,r.firstname,r.year
          FROM guard_assignments g LEFT JOIN residents r ON r.id=g.resident_id
          WHERE substr(g.roster_date,1,7)=? AND g.active=1
          ORDER BY g.roster_date,g.sector,g.raw_label
        """, (month,)).fetchall()
        c.close()
        output = io.StringIO()
        writer = csv.writer(output, delimiter=";")
        writer.writerow(["Date", "Service", "Libellé source", "Résident validé", "Année", "Horaire", "Statut"])
        for row in rows:
            writer.writerow([row["roster_date"], row["sector"], row["raw_label"],
                             ((row["surname"] or "") + " " + (row["firstname"] or "")).strip(),
                             row["year"] or "", row["hours"], row["mapping_status"]])
        data = io.BytesIO(("\ufeff" + output.getvalue()).encode("utf-8"))
        return send_file(data, mimetype="text/csv; charset=utf-8", as_attachment=True,
                         download_name=f"gardes_{month}.csv")
