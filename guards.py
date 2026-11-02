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
          AND NOT EXISTS (SELECT 1 FROM dems_archive d WHERE d.resident_id=r.id)
        ORDER BY r.year DESC,r.surname COLLATE NOCASE,r.firstname COLLATE NOCASE
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
                if action == "delete":
                    assignment_id = int(request.form.get("assignment_id", "0"))
                    row = c.execute("SELECT * FROM guard_assignments WHERE id=?", (assignment_id,)).fetchone()
                    if not row:
                        raise ValueError("Affectation de garde introuvable.")
                    c.execute("DELETE FROM guard_assignments WHERE id=?", (assignment_id,))
                    audit_event(c, "guards.assignment_deleted",
                                f"id={assignment_id}; date={row['roster_date']}; sector={row['sector']}; label={row['raw_label']}")
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
                      WHERE roster_date=? AND sector=? AND
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
          WHERE substr(g.roster_date,1,7)=?
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
        residents = _eligible_residents(c)
        source = c.execute("SELECT * FROM guard_sources WHERE month=?", (month,)).fetchone()
        c.close()
        return page("""<section class="rt-guards-hero">
          <div class="rt-guards-heading"><div><p class="rt-kicker">RESIMANAGE · PLANNING</p>
          <h1>🛡️ {{L('Gestion des gardes','Guard management','تسيير المناوبات')}}</h1>
          <p>{{L('Calendrier mensuel · UMC et Réanimation chirurgicale','Monthly calendar · Emergency and surgical intensive care','تقويم شهري · الاستعجالات والإنعاش الجراحي')}}</p></div>
          <div class="rt-guards-month"><form method="get"><label>{{L('Mois affiché','Displayed month','الشهر المعروض')}}</label><select name="month" onchange="this.form.submit()">{% for item in month_options %}<option value="{{item.value}}" {% if item.value==month %}selected{% endif %}>{{item.label}}</option>{% endfor %}</select></form></div></div>
          <div class="rt-guards-stats"><div><strong>{{counts.total}}</strong><span>{{L('Affectations','Assignments','التعيينات')}}</span></div><div><strong>{{counts.validated}}</strong><span>{{L('Identités validées','Validated identities','هويات مؤكدة')}}</span></div><div class="is-warning"><strong>{{counts.unresolved}}</strong><span>{{L('À identifier','To identify','تحتاج إلى تحديد')}}</span></div></div>
          {% if source %}<p class="rt-source-note">📚 {{L('Mois importé depuis le planning historique :','Month imported from historical roster:','شهر مستورد من جدول المناوبات التاريخي:')}} {{source.title}} · <a href="/guards/source/{{source.id}}">{{L('Voir la source','View source','عرض المصدر')}}</a></p>{% endif %}
          {% if month=='2026-10' %}<p class="rt-history-note">🔒 {{L('Planning historique importé. Les libellés d’origine sont conservés ; aucune identité n’a été attribuée automatiquement.','Historical roster imported. Original labels are preserved; no identity was assigned automatically.','تم استيراد الجدول التاريخي مع الحفاظ على التسميات الأصلية؛ لم يتم إسناد أي هوية تلقائيًا.')}}</p>{% elif counts.total==0 %}<p class="rt-draft-note">✎ {{L('Mois vierge : aucune garde n’a été générée. Ajoutez les affectations après validation du roulement.','Empty month: no shifts have been generated. Add assignments only after validating the rotation rules.','شهر فارغ: لم يتم إنشاء أي مناوبة. أضف التعيينات بعد التحقق من قواعد التناوب.')}}</p>{% endif %}
        </section>
        {% if role=='super_admin' %}<section id="guard-add" class="rt-guard-editor"><h2>{{L('Ajouter une affectation','Add an assignment','إضافة تعيين')}}</h2>
          <form method="post" class="rt-guard-add-form"><input type="hidden" name="month" value="{{month}}"><input type="hidden" name="action" value="add">
            <label>{{L('Date','Date','التاريخ')}}<input type="date" name="roster_date" min="{{month}}-01" max="{{month}}-{{'%02d'|format(days|length)}}" required></label>
            <label>{{L('Service','Department','المصلحة')}}<select name="sector"><option>UMC</option><option>Réanimation chirurgicale</option></select></label>
            <label>{{L('Résident identifié (facultatif)','Identified resident (optional)','مقيم محدد (اختياري)')}}<select name="resident_id"><option value="">{{L('Saisir un libellé historique / non identifié','Enter an unresolved / historical label','أدخل تسمية غير محددة')}}</option>{% for r in residents %}<option value="{{r.id}}">{{r.surname}} {{r.firstname}} · {{r.year}}{{L('e année','th year',' سنة')}}</option>{% endfor %}</select></label>
            <label>{{L('Nom / libellé si non identifié','Name / label if not identified','الاسم / التسمية إن لم تكن محددة')}}<input name="raw_label" maxlength="120" placeholder="{{L('Ex. NOM ou NOM Prénom','e.g. SURNAME or SURNAME First name','مثال: اللقب والاسم')}}"></label>
            <label>{{L('Horaire','Hours','التوقيت')}}<select name="hours"><option value="16H-08H">16H-08H</option><option value="08H-08H">08H-08H</option></select></label>
            <button type="submit">＋ {{L('Ajouter au calendrier','Add to calendar','إضافة إلى التقويم')}}</button>
          </form></section>{% endif %}
        <section class="rt-guard-calendar-section"><div class="rt-guard-calendar-title"><h2>{{month_label}}</h2><a class="button" href="/guards/mapping?month={{month}}">👤 {{L('Identifier les résidents','Identify residents','تحديد المقيمين')}}</a><a class="button" href="/guards/export.csv?month={{month}}">⬇ CSV</a></div>
          <div class="wrap"><table class="rt-guard-calendar"><thead><tr><th>{{L('Jour','Day','اليوم')}}</th><th>{{L('UMC','Emergency','الاستعجالات')}}</th><th>{{L('Réanimation chirurgicale','Surgical ICU','الإنعاش الجراحي')}}</th></tr></thead><tbody>
          {% for day in days %}<tr class="{% if day.weekend %}rt-weekend{% endif %}"><th><strong>{{day.day}}</strong><span>{{day.weekday}}</span><small>{{day.date[8:10]}}/{{day.date[5:7]}}/{{day.date[:4]}}</small></th>
            {% for sector,items in [('UMC',day.umc),('Réanimation chirurgicale',day.surgical)] %}<td><div class="rt-guard-cell"><div class="rt-guard-hours">{{items[0].hours if items else day.hours}}</div>
              {% for item in items %}<div class="rt-guard-person {% if item.mapping_status!='validated' %}is-unresolved{% endif %}"><span>{{(item.surname~' '~item.firstname) if item.resident_id else item.raw_label}}</span>{% if item.resident_id %}<small>{{item.year}}{{L('e année','th year',' سنة')}}</small>{% else %}<small>{{L('À identifier','Unresolved','غير محدد')}}</small>{% endif %}
                {% if role=='super_admin' %}<form method="post"><input type="hidden" name="month" value="{{month}}"><input type="hidden" name="action" value="delete"><input type="hidden" name="assignment_id" value="{{item.id}}"><button title="{{L('Retirer','Remove','إزالة')}}" aria-label="{{L('Retirer','Remove','إزالة')}}">×</button></form>{% endif %}</div>{% endfor %}
              {% if not items %}<span class="rt-guard-empty">{{L('Aucune affectation','No assignment','لا يوجد تعيين')}}</span>{% endif %}</div></td>{% endfor %}
          </tr>{% endfor %}</tbody></table></div>
          <p class="rt-guard-footnote">{{L('Les gardes du vendredi et du samedi sont affichées en 08H–08H ; les autres jours en 16H–08H, conformément au planning d’octobre 2026. Vérifiez l’horaire avant toute nouvelle saisie.','Friday and Saturday shifts are shown as 08H–08H; other days as 16H–08H, matching the October 2026 source. Verify hours before adding new entries.','مناوبات الجمعة والسبت من 08 إلى 08؛ وبقية الأيام من 16 إلى 08، وفق جدول أكتوبر 2026. تحقق من التوقيت قبل إضافة تعيينات جديدة.')}}</p>
        </section>
        <style>
        .rt-guards-hero{background:linear-gradient(130deg,#092b50,#135b83 58%,#126c70)!important;color:#effaff!important;border:1px solid #65d8ef!important}
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
        @media(max-width:680px){.rt-guard-add-form{grid-template-columns:1fr}.rt-guard-add-form button{grid-column:1}.rt-guards-stats strong{font-size:21px}.rt-guards-stats span{font-size:10px}.rt-guard-calendar-title{align-items:stretch}.rt-guard-calendar-title a{flex:1;text-align:center}}
        </style>""", month=month, month_label=_month_label(month), month_options=month_options,
                    days=days, counts=counts, source=source, residents=residents)

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
        global_labels = c.execute("""
          SELECT raw_label,COUNT(*) AS occurrences,MAX(resident_id) AS resident_id
          FROM guard_assignments GROUP BY raw_label ORDER BY raw_label COLLATE NOCASE
        """).fetchall()
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
          <h2>{{source.title}}</h2><p>{{L('Fichier','File','الملف')}} : {{source.filename}}</p>
          <p>{{L('Importé le','Imported on','تاريخ الاستيراد')}} : {{source.imported_at}}</p>
          <p>{{L('Empreinte SHA-256','SHA-256 fingerprint','بصمة SHA-256')}} : <code>{{source.source_sha256}}</code></p>
          <p>{{L('Les données importées sont conservées séparément des modifications du calendrier.','Imported data is preserved separately from calendar edits.','يتم الاحتفاظ بالبيانات المستوردة بشكل منفصل عن تعديلات التقويم.')}}</p>
          <a class="button" href="/guards?month={{source.month}}">← {{L('Retour','Back','عودة')}}</a></section>""", source=source)

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
          WHERE substr(g.roster_date,1,7)=?
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
