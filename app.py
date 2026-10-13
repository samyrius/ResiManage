# -*- coding: utf-8 -*-
from flask import Flask, request, redirect, session, render_template_string, flash, send_file
import sqlite3, os, hashlib, hmac, io, csv, shutil, secrets
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

BASE=os.path.dirname(os.path.abspath(__file__))
DB=os.path.join(BASE,"rotation.db")
app=Flask(__name__)
app.secret_key=os.environ.get("ROTATION_SECRET") or secrets.token_hex(32)
app.config.update(
 SESSION_COOKIE_HTTPONLY=True,
 SESSION_COOKIE_SAMESITE="Lax",
 SESSION_COOKIE_SECURE=os.environ.get("ROTATION_COOKIE_SECURE")=="1",
)
LANGS=("ar","fr","en")
D={
"ar":{"app":"تسيير تربصات الأطباء المقيمين","home":"الرئيسية","residents":"المقيمون","terrains":"المصالح","capacities":"المقاعد","assign":"التوزيع","history":"التاريخ","summary":"ملخص المقيمين","decisions":"القرارات","settings":"الإعدادات","logout":"خروج","login":"دخول المسؤول","password":"كلمة المرور","setup_password":"أنشئ كلمة مرور للمسؤول (12 حرفًا على الأقل).","setup_password_error":"يجب أن تكون كلمة المرور 12 حرفًا على الأقل وأن يتطابق التأكيد.","password_confirm":"تأكيد كلمة المرور","signin":"دخول","badpass":"كلمة المرور غير صحيحة","year":"السنة الجامعية","resident":"المقيم","surname":"اللقب","firstname":"الاسم","study_year":"السنة","phone":"الهاتف","repeat":"يعيد السنة","status":"الحالة","active":"نشط","inactive":"غير نشط","add":"إضافة","save":"حفظ","terrain":"المصلحة","kind":"النوع","mandatory":"إجباري","basic":"أساسي","optional":"اختياري","mandatory_year":"السنة الإلزامية","any":"حسب البرنامج","period":"الفترة","places":"عدد المقاعد","used":"المستعمل","remaining":"المتبقي","date":"تاريخ الإنجاز","academic_year":"السنة الجامعية","choose":"اختيار","assign_now":"تعيين مقيم","check_save":"التحقق والحفظ","confirmed":"مؤكد","pending":"بانتظار القرار","rejected":"مرفوض","history_add":"تسجيل تربص سابق","reason":"سبب القرار","approve":"موافقة","reject":"رفض","language":"لغة الواجهة","director":"المسؤول","new_password":"كلمة مرور جديدة (اختياري)","change":"حفظ الإعدادات","note":"تغيير اللغة لا يغيّر البيانات المحفوظة.","priority":"الأولوية للسنة الرابعة ثم الثالثة والثانية والأولى.","none":"لا توجد بيانات","capacity_first":"حدّد السعة أولاً لهذه المصلحة والفترة","full":"السعة مكتملة","duplicate":"المقيم مسجّل في نفس الفترة بمصلحة: ","same_terrain_year":"سبق للمقيم إنجاز هذه المصلحة خلال السنة الجامعية في الفترة: ","history_block":"التربص منجز سابقاً؛ يمنع التكرار حتى إكمال جميع المصالح.","history_repeat":"يمكن التكرار لأن المقيم أكمل جميع المصالح.","mismatch":"السنة لا تطابق السنة الإلزامية؛ التعيين بانتظار قرار المسؤول","done":"تم الحفظ","overview":"ملخص التوزيع السنوي","count":"عدد التعيينات","type":"التصنيف","export":"تصدير CSV","backup":"تنزيل نسخة احتياطية","all":"كل المصالح","four":"التعيينات المؤكدة / 4 فترات","waiting":"معلّق"},
"fr":{"app":"Gestion des stages des médecins résidents","home":"Accueil","residents":"Résidents","terrains":"Services","capacities":"Capacités","assign":"Affectations","history":"Historique","summary":"Bilan résidents","decisions":"Décisions","settings":"Paramètres","logout":"Déconnexion","login":"Connexion administrateur","password":"Mot de passe","setup_password":"Créez un mot de passe administrateur (12 caractères minimum).","setup_password_error":"Le mot de passe doit contenir au moins 12 caractères et les confirmations doivent correspondre.","password_confirm":"Confirmer le mot de passe","signin":"Connexion","badpass":"Mot de passe incorrect","year":"Année universitaire","resident":"Résident","surname":"Nom","firstname":"Prénom","study_year":"Année","phone":"Téléphone","repeat":"Redouble","status":"Statut","active":"Actif","inactive":"Inactif","add":"Ajouter","save":"Enregistrer","terrain":"Service","kind":"Type","mandatory":"Obligatoire","basic":"De base","optional":"Optionnel","mandatory_year":"Année requise","any":"Selon le programme","period":"Période","places":"Nombre de places","used":"Utilisées","remaining":"Restantes","date":"Date de réalisation","academic_year":"Année universitaire","choose":"Choisir","assign_now":"Affecter un résident","check_save":"Vérifier et enregistrer","confirmed":"Confirmé","pending":"En attente","rejected":"Refusé","history_add":"Enregistrer un stage antérieur","reason":"Motif de décision","approve":"Approuver","reject":"Refuser","language":"Langue de l’interface","director":"Responsable","new_password":"Nouveau mot de passe (facultatif)","change":"Enregistrer les paramètres","note":"Changer de langue ne modifie pas les données.","priority":"Priorité aux 4e, puis 3e, 2e et 1re années.","none":"Aucune donnée","capacity_first":"Définissez d’abord la capacité du service et de la période","full":"Capacité complète","duplicate":"Résident déjà affecté pendant cette période au service : ","same_terrain_year":"Ce résident a déjà effectué ce service cette année, pendant la période : ","history_block":"Stage déjà effectué ; répétition bloquée avant d’avoir terminé tous les services.","history_repeat":"Répétition autorisée : tous les services ont été effectués.","mismatch":"Année différente de l’année requise ; décision du responsable nécessaire","done":"Enregistré","overview":"Vue annuelle des affectations","count":"Nombre d’affectations","type":"Catégorie","export":"Exporter CSV","backup":"Télécharger la sauvegarde","all":"Tous les services","four":"Affectations confirmées / 4 périodes","waiting":"En attente"},
"en":{"app":"Resident Rotation Manager","home":"Home","residents":"Residents","terrains":"Departments","capacities":"Capacity","assign":"Assignments","history":"History","summary":"Resident summary","decisions":"Decisions","settings":"Settings","logout":"Log out","login":"Administrator login","password":"Password","setup_password":"Create an administrator password (at least 12 characters).","setup_password_error":"The password must be at least 12 characters and both entries must match.","password_confirm":"Confirm password","signin":"Sign in","badpass":"Incorrect password","year":"Academic year","resident":"Resident","surname":"Surname","firstname":"First name","study_year":"Year","phone":"Phone","repeat":"Repeating year","status":"Status","active":"Active","inactive":"Inactive","add":"Add","save":"Save","terrain":"Department","kind":"Type","mandatory":"Mandatory","basic":"Core","optional":"Optional","mandatory_year":"Required year","any":"As per curriculum","period":"Period","places":"Places","used":"Used","remaining":"Remaining","date":"Completion date","academic_year":"Academic year","choose":"Choose","assign_now":"Assign resident","check_save":"Validate and save","confirmed":"Confirmed","pending":"Pending decision","rejected":"Rejected","history_add":"Record previous rotation","reason":"Decision reason","approve":"Approve","reject":"Reject","language":"Interface language","director":"Administrator","new_password":"New password (optional)","change":"Save settings","note":"Changing language does not change saved data.","priority":"Priority: year 4, then 3, 2 and 1.","none":"No data","capacity_first":"Set capacity for this department and period first","full":"Capacity is full","duplicate":"Resident already assigned during this period to: ","same_terrain_year":"This resident already completed this department this academic year, during: ","history_block":"Rotation completed previously; repeats blocked until all departments are completed.","history_repeat":"Repeat allowed because all departments have been completed.","mismatch":"Year does not match required year; administrator decision needed","done":"Saved","overview":"Annual assignment overview","count":"Assignment count","type":"Category","export":"Export CSV","backup":"Download backup","all":"All departments","four":"Confirmed assignments / 4 periods","waiting":"Pending"}
}
def tr(k): return D.get(session.get("lang","ar"),D["ar"]).get(k,D["ar"].get(k,k))
def db():
 c=sqlite3.connect(DB,timeout=20); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c
def setting(c,k,default=""):
 r=c.execute("SELECT value FROM settings WHERE key=?",(k,)).fetchone(); return r["value"] if r else default
def init():
 c=db()
 c.executescript("""
 CREATE TABLE IF NOT EXISTS residents(id INTEGER PRIMARY KEY,surname TEXT NOT NULL,firstname TEXT NOT NULL,year INTEGER NOT NULL CHECK(year BETWEEN 1 AND 4),phone TEXT DEFAULT '',repeat_year INTEGER DEFAULT 0,status TEXT DEFAULT 'active');
 CREATE TABLE IF NOT EXISTS terrains(id INTEGER PRIMARY KEY,name TEXT UNIQUE NOT NULL,kind TEXT DEFAULT 'basic',mandatory_year INTEGER DEFAULT 0);
 CREATE TABLE IF NOT EXISTS periods(id INTEGER PRIMARY KEY,year_label TEXT NOT NULL,name TEXT NOT NULL,UNIQUE(year_label,name));
 CREATE TABLE IF NOT EXISTS capacities(id INTEGER PRIMARY KEY,year_label TEXT NOT NULL,terrain_id INTEGER,period_id INTEGER,places INTEGER NOT NULL,UNIQUE(year_label,terrain_id,period_id));
 CREATE TABLE IF NOT EXISTS assignments(id INTEGER PRIMARY KEY,resident_id INTEGER,terrain_id INTEGER,period_id INTEGER,status TEXT DEFAULT 'confirmed',UNIQUE(resident_id,period_id));
 CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY,resident_id INTEGER,terrain_id INTEGER,year_label TEXT,period TEXT,date_done TEXT);
 CREATE TABLE IF NOT EXISTS decisions(id INTEGER PRIMARY KEY,details TEXT,decision TEXT,reason TEXT,actor TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
 CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,action TEXT,details TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
 CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
 """)
 y=str(datetime.now().year)+"-"+str(datetime.now().year+1)
 c.execute("INSERT OR IGNORE INTO settings VALUES('year',?)",(y,))
 initial_password=os.environ.get("ROTATION_INITIAL_PASSWORD")
 if initial_password:
  c.execute("INSERT OR IGNORE INTO settings VALUES('password',?)",(generate_password_hash(initial_password),))
 c.execute("INSERT OR IGNORE INTO settings VALUES('director',?)",("Professor Benhocine",))
 for n,k in [("Réanimation chirurgicale","basic"),("Réanimation polyvalente","basic"),("Chirurgie générale","mandatory"),("Urologie","basic"),("Orthopédie","basic"),("Neurochirurgie","basic"),("Sédation","optional"),("Maxillo-faciale","basic"),("CCI","basic"),("Obstétrique","basic"),("Chirurgie cardiaque","basic"),("PU Médecine","basic"),("PU Chirurgie","basic"),("ORL","basic"),("Ophtalmologie","basic"),("Gynécologie","basic"),("Chirurgie thoracique","basic"),("Brûlés","basic")]:
  c.execute("INSERT OR IGNORE INTO terrains(name,kind) VALUES(?,?)",(n,k))
 y=setting(c,"year",y)
 if not c.execute("SELECT 1 FROM periods WHERE year_label=?",(y,)).fetchone():
  for n in ["01 Fév - 30 Avr","01 Mai - 30 Juillet","01 Août - 30 Oct","01 Nov - 30 Jan"]:
   c.execute("INSERT OR IGNORE INTO periods(year_label,name) VALUES(?,?)",(y,n))
 c.commit(); c.close()
@app.before_request
def boot():
 if not getattr(app,"_ready",False): init(); app._ready=True

@app.before_request
def verify_csrf():
 if request.method=="POST":
  expected=session.get("_csrf_token","")
  supplied=request.form.get("_csrf_token","")
  if not expected or not supplied or not hmac.compare_digest(expected,supplied):
   return "Invalid or missing CSRF token",400
def page(body,**kw):
 lang=session.get("lang","ar")
 shell="""<!doctype html><html lang="{{lang}}" dir="{{'rtl' if lang=='ar' else 'ltr'}}"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{t('app')}}</title><style>body{font-family:Arial,sans-serif;background:#f1f5f9;margin:0;color:#182b3d}header{background:#164e83;color:white;padding:15px}main{max-width:1050px;margin:auto;padding:12px}nav{display:flex;gap:6px;overflow:auto;background:white;padding:10px}a,button{background:#164e83;color:white;padding:9px 12px;border:0;border-radius:7px;text-decoration:none;display:inline-block;white-space:nowrap}section{background:white;padding:13px;border:1px solid #d7e1eb;border-radius:10px;margin:10px 0}input,select{font:inherit;padding:9px;border:1px solid #bccada;border-radius:7px;width:100%;box-sizing:border-box;margin:4px 0 9px}label{display:block}table{border-collapse:collapse;width:100%;min-width:540px}td,th{text-align:start;border-bottom:1px solid #ddd;padding:8px}.wrap{overflow:auto}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px}.msg{background:#fff0c2;padding:10px;border-radius:7px}.good{color:green}.bad{color:#b21d1d}.muted{color:#526274}@media(max-width:600px){main{padding:7px}header{font-size:14px}}</style><header><h2>{{t('app')}}</h2>{{t('year')}}: {{year}}</header>{% if user %}<nav><a href="/">{{t('home')}}</a><a href="/residents">{{t('residents')}}</a><a href="/terrains">{{t('terrains')}}</a><a href="/capacities">{{t('capacities')}}</a><a href="/assign">{{t('assign')}}</a><a href="/history">{{t('history')}}</a><a href="/summary">{{t('summary')}}</a><a href="/decisions">{{t('decisions')}}</a><a href="/settings">{{t('settings')}}</a><a href="/export">{{t('export')}}</a><a href="/backup">{{t('backup')}}</a><a href="/logout">{{t('logout')}}</a></nav>{% endif %}<main>{% for m in get_flashed_messages() %}<p class="msg">{{m}}</p>{% endfor %}{{body|safe}}</main></html>"""
 context={"t":tr,"lang":lang,"year":setting(db(),"year")}
 context.update(kw)
 context.setdefault("csrf_token",session.setdefault("_csrf_token",secrets.token_urlsafe(32)))
 inner=render_template_string(body,**context)
 return render_template_string(shell,body=inner,lang=lang,t=tr,year=setting(db(),"year"),user=bool(session.get("user")))
def guard():
 if not session.get("user"): return redirect("/login")
@app.get("/lang/<lang>")
def lang(lang):
 if lang in LANGS: session["lang"]=lang
 return redirect(request.referrer or "/login")
@app.route("/login",methods=["GET","POST"])
def login():
 c=db(); p=setting(c,"password"); c.close()
 if request.method=="POST":
  submitted=request.form.get("password","")
  if not p:
   if len(submitted)<12 or submitted!=request.form.get("password_confirm",""):
    flash(tr("setup_password_error"))
   else:
    c=db(); c.execute("INSERT INTO settings(key,value) VALUES('password',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(generate_password_hash(submitted),)); c.commit(); c.close()
    session.clear(); session["user"]="admin"; return redirect("/")
  else:
   modern_hash=p.startswith(("scrypt:","pbkdf2:"))
   valid=check_password_hash(p,submitted) if modern_hash else hmac.compare_digest(hashlib.sha256(submitted.encode()).hexdigest(),p)
   if valid:
    if not modern_hash:
     c=db(); c.execute("UPDATE settings SET value=? WHERE key='password'",(generate_password_hash(submitted),)); c.commit(); c.close()
    session.clear(); session["user"]="admin"; return redirect("/")
   flash(tr("badpass"))
 return page("""<section><p><a href="/lang/ar">العربية</a> <a href="/lang/fr">Français</a> <a href="/lang/en">English</a></p><h3>{{t('login')}}</h3>{% if not configured %}<p>{{t('setup_password')}}</p>{% endif %}<form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><label>{{t('password')}}</label><input name="password" type="password" minlength="12" required>{% if not configured %}<label>{{t('password_confirm')}}</label><input name="password_confirm" type="password" minlength="12" required>{% endif %}<button>{{t('signin')}}</button></form></section>""",configured=bool(p))
@app.get("/logout")
def logout(): session.clear(); return redirect("/login")
@app.get("/")
def home():
 if guard(): return redirect("/login")
 c=db(); y=setting(c,"year"); rs=c.execute("SELECT * FROM residents WHERE status='active' ORDER BY year DESC,surname").fetchall()
 count=c.execute("SELECT COUNT(*) FROM terrains").fetchone()[0]; confirmed=c.execute("SELECT COUNT(*) FROM assignments a JOIN periods p ON p.id=a.period_id WHERE p.year_label=? AND a.status='confirmed'",(y,)).fetchone()[0]
 rows=[]
 for r in rs:
  n=c.execute("SELECT COUNT(*) FROM assignments a JOIN periods p ON p.id=a.period_id WHERE a.resident_id=? AND p.year_label=? AND a.status='confirmed'",(r["id"],y)).fetchone()[0]; rows.append((r,n))
 c.close()
 return page("""<section><h3>{{t('overview')}}</h3><p>{{t('priority')}}</p><p>{{t('residents')}}: {{rows|length}} · {{t('terrains')}}: {{count}} · {{t('confirmed')}}: {{confirmed}}</p></section><section><h3>{{t('four')}}</h3><div class="wrap"><table><tr><th>{{t('resident')}}</th><th>{{t('study_year')}}</th><th>{{t('count')}}</th></tr>{% for r,n in rows %}<tr><td>{{r.surname}} {{r.firstname}}</td><td>{{r.year}}</td><td>{{n}} / 4</td></tr>{% endfor %}</table></div></section>""",rows=rows,count=count,confirmed=confirmed)
@app.route("/residents",methods=["GET","POST"])
def residents():
 if guard(): return redirect("/login")
 c=db()
 if request.method=="POST":
  if request.form.get("action")=="edit":
   c.execute("UPDATE residents SET year=?,repeat_year=?,status=? WHERE id=?",(int(request.form["year"]),int(request.form.get("repeat_year","0")),request.form["status"],int(request.form["rid"])))
  else:
   c.execute("INSERT INTO residents(surname,firstname,year,phone,repeat_year,status) VALUES(?,?,?,?,?,?)",(request.form["surname"].strip(),request.form["firstname"].strip(),int(request.form["year"]),request.form.get("phone",""),int(request.form.get("repeat_year","0")),"active"))
  c.commit(); flash(tr("done"))
 rows=c.execute("SELECT * FROM residents ORDER BY status DESC,year DESC,surname").fetchall(); c.close()
 return page("""<section><h3>{{t('add')}} — {{t('resident')}}</h3><form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><div class="grid"><div><label>{{t('surname')}}</label><input name="surname" required></div><div><label>{{t('firstname')}}</label><input name="firstname" required></div><div><label>{{t('study_year')}}</label><select name="year">{% for y in range(1,5) %}<option>{{y}}</option>{% endfor %}</select></div><div><label>{{t('phone')}}</label><input name="phone"></div></div><label><input type="checkbox" name="repeat_year" value="1"> {{t('repeat')}}</label><button>{{t('add')}}</button></form></section><section><div class="wrap"><table><tr><th>{{t('resident')}}</th><th>{{t('study_year')}}</th><th>{{t('save')}}</th></tr>{% for r in rows %}<tr><td>{{r.surname}} {{r.firstname}}</td><td>{{r.year}}</td><td><form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><input type="hidden" name="action" value="edit"><input type="hidden" name="rid" value="{{r.id}}"><select name="year">{% for y in range(1,5) %}<option value="{{y}}" {% if r.year==y %}selected{% endif %}>{{y}}</option>{% endfor %}</select><label><input type="checkbox" name="repeat_year" value="1" {% if r.repeat_year %}checked{% endif %}> {{t('repeat')}}</label><select name="status"><option value="active">{{t('active')}}</option><option value="inactive">{{t('inactive')}}</option></select><button>{{t('save')}}</button></form></td></tr>{% endfor %}</table></div></section>""",rows=rows)
@app.route("/terrains",methods=["GET","POST"])
def terrains():
 if guard(): return redirect("/login")
 c=db()
 if request.method=="POST":
  try: c.execute("INSERT INTO terrains(name,kind,mandatory_year) VALUES(?,?,?)",(request.form["name"].strip(),request.form["kind"],int(request.form["mandatory_year"]))); c.commit(); flash(tr("done"))
  except sqlite3.IntegrityError: flash("Already exists / Existe déjà / المصلحة موجودة")
 rows=c.execute("SELECT * FROM terrains ORDER BY CASE WHEN kind='optional' THEN 1 ELSE 0 END, name").fetchall(); c.close()
 return page("""<section><h3>{{t('add')}} — {{t('terrain')}}</h3><form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><label>{{t('terrain')}}</label><input name="name" required><div class="grid"><div><label>{{t('kind')}}</label><select name="kind"><option value="mandatory">{{t('mandatory')}}</option><option value="basic">{{t('basic')}}</option><option value="optional">{{t('optional')}}</option></select></div><div><label>{{t('mandatory_year')}}</label><select name="mandatory_year"><option value="0">{{t('any')}}</option>{% for y in range(1,5) %}<option value="{{y}}">{{y}}</option>{% endfor %}</select></div></div><button>{{t('save')}}</button></form></section><section><div class="wrap"><table><tr><th>{{t('terrain')}}</th><th>{{t('kind')}}</th><th>{{t('mandatory_year')}}</th></tr>{% for r in rows %}<tr><td>{{r.name}}</td><td>{{t(r.kind)}}</td><td>{{r.mandatory_year or t('any')}}</td></tr>{% endfor %}</table></div></section>""",rows=rows)
@app.route("/capacities",methods=["GET","POST"])
def capacities():
 if guard(): return redirect("/login")
 c=db(); y=setting(c,"year")
 if request.method=="POST":
  tid,pid,places=int(request.form["terrain"]),int(request.form["period"]),max(0,int(request.form["places"]))
  used=c.execute("SELECT COUNT(*) FROM assignments WHERE terrain_id=? AND period_id=? AND status IN ('confirmed','pending')",(tid,pid)).fetchone()[0]
  if places<used: flash(tr("full"))
  else:
   c.execute("INSERT INTO capacities(year_label,terrain_id,period_id,places) VALUES(?,?,?,?) ON CONFLICT(year_label,terrain_id,period_id) DO UPDATE SET places=excluded.places",(y,tid,pid,places)); c.commit(); flash(tr("done"))
 ts=c.execute("SELECT * FROM terrains ORDER BY CASE WHEN kind='optional' THEN 1 ELSE 0 END, name").fetchall(); ps=c.execute("SELECT * FROM periods WHERE year_label=? ORDER BY id",(y,)).fetchall()
 rows=c.execute("SELECT t.name terrain,p.name period,cap.places,(SELECT COUNT(*) FROM assignments a WHERE a.terrain_id=t.id AND a.period_id=p.id AND a.status IN ('confirmed','pending')) used FROM capacities cap JOIN terrains t ON t.id=cap.terrain_id JOIN periods p ON p.id=cap.period_id WHERE cap.year_label=?",(y,)).fetchall(); c.close()
 return page("""<section><h3>{{t('capacities')}}</h3><form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><div class="grid"><div><label>{{t('terrain')}}</label><select name="terrain">{% for x in ts %}<option value="{{x.id}}">{{x.name}}</option>{% endfor %}</select></div><div><label>{{t('period')}}</label><select name="period">{% for x in ps %}<option value="{{x.id}}">{{x.name}}</option>{% endfor %}</select></div><div><label>{{t('places')}}</label><input type="number" min="0" name="places" required></div></div><button>{{t('save')}}</button></form></section><section><div class="wrap"><table><tr><th>{{t('period')}}</th><th>{{t('terrain')}}</th><th>{{t('places')}}</th><th>{{t('used')}}</th><th>{{t('remaining')}}</th></tr>{% for r in rows %}<tr><td>{{r.period}}</td><td>{{r.terrain}}</td><td>{{r.places}}</td><td>{{r.used}}</td><td>{{r.places-r.used}}</td></tr>{% endfor %}</table></div></section>""",ts=ts,ps=ps,rows=rows)
def check(c,rid,tid,pid,y):
 r=c.execute("SELECT * FROM residents WHERE id=? AND status='active'",(rid,)).fetchone(); t=c.execute("SELECT * FROM terrains WHERE id=?",(tid,)).fetchone(); p=c.execute("SELECT * FROM periods WHERE id=? AND year_label=?",(pid,y)).fetchone()
 if not r or not t or not p: return False,tr("none"),None
 dup=c.execute("SELECT t.name FROM assignments a JOIN terrains t ON t.id=a.terrain_id WHERE a.resident_id=? AND a.period_id=? AND a.status IN ('confirmed','pending')",(rid,pid)).fetchone()
 if dup:return False,tr("duplicate")+dup["name"],None
 repeat = c.execute(
  "SELECT t.name,p.name AS period FROM assignments a JOIN terrains t ON t.id=a.terrain_id JOIN periods p ON p.id=a.period_id WHERE a.resident_id=? AND a.terrain_id=? AND p.year_label=? AND a.period_id<>? AND a.status IN ('confirmed','pending') LIMIT 1",
  (rid,tid,y,pid)
 ).fetchone()
 total=c.execute(
  "SELECT COUNT(*) FROM terrains WHERE kind IN ('mandatory','basic')"
 ).fetchone()[0]
 done=c.execute("""
  SELECT COUNT(DISTINCT terrain_id) FROM (
   SELECT h.terrain_id FROM history h
   JOIN terrains t ON t.id=h.terrain_id
   WHERE h.resident_id=? AND t.kind IN ('mandatory','basic')
   UNION
   SELECT a.terrain_id FROM assignments a
   JOIN terrains t ON t.id=a.terrain_id
   WHERE a.resident_id=? AND a.status='confirmed'
   AND t.kind IN ('mandatory','basic')
  )
 """,(rid,rid)).fetchone()[0]
 if repeat and done<total:
  return False,tr("same_terrain_year")+repeat["name"]+" — "+repeat["period"],None
 cap=c.execute("SELECT places FROM capacities WHERE year_label=? AND terrain_id=? AND period_id=?",(y,tid,pid)).fetchone()
 if not cap:return False,tr("capacity_first"),None
 used=c.execute("SELECT COUNT(*) FROM assignments WHERE terrain_id=? AND period_id=? AND status IN ('confirmed','pending')",(tid,pid)).fetchone()[0]
 if used>=cap["places"]:return False,tr("full"),None
 h=c.execute("SELECT year_label,period,date_done FROM history WHERE resident_id=? AND terrain_id=? ORDER BY id DESC LIMIT 1",(rid,tid)).fetchone()
 if h and done<total:return False,tr("history_block")+f" ({h['year_label']} / {h['period']} / {h['date_done']})",None
 if t["mandatory_year"] and t["mandatory_year"]!=r["year"]:return True,tr("mismatch"),"pending"
 return True,(tr("history_repeat") if h else tr("done")),"confirmed"
@app.route("/assign",methods=["GET","POST"])
def assign():
 if guard():return redirect("/login")
 c=db(); y=setting(c,"year")
 if request.method=="POST":
  try:
   rid,tid,pid=map(int,(request.form["resident"],request.form["terrain"],request.form["period"])); ok,msg,status=check(c,rid,tid,pid,y)
   if not ok: flash(msg)
   else:
    old=c.execute("SELECT id,status FROM assignments WHERE resident_id=? AND period_id=?",(rid,pid)).fetchone()
    if old and old["status"] not in ("rejected","cancelled"): flash(tr("duplicate"))
    elif old:c.execute("UPDATE assignments SET terrain_id=?,status=? WHERE id=?",(tid,status,old["id"])); c.commit(); flash(msg)
    else:c.execute("INSERT INTO assignments(resident_id,terrain_id,period_id,status) VALUES(?,?,?,?)",(rid,tid,pid,status)); c.commit(); flash(msg)
  except Exception: c.rollback(); flash("Invalid assignment / Affectation invalide / تعيين غير صالح")
 rs=c.execute("SELECT * FROM residents WHERE status='active' ORDER BY year DESC,surname").fetchall(); ts=c.execute("SELECT * FROM terrains ORDER BY CASE WHEN kind='optional' THEN 1 ELSE 0 END, name").fetchall(); ps=c.execute("SELECT * FROM periods WHERE year_label=? ORDER BY id",(y,)).fetchall()
 rows=c.execute("SELECT a.*,r.surname,r.firstname,r.year,t.name terrain,p.name period FROM assignments a JOIN residents r ON r.id=a.resident_id JOIN terrains t ON t.id=a.terrain_id JOIN periods p ON p.id=a.period_id WHERE p.year_label=? ORDER BY p.id,r.year DESC",(y,)).fetchall(); c.close()
 return page("""<section><h3>{{t('assign_now')}}</h3><p>{{t('priority')}}</p><form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><label>{{t('resident')}}</label><select name="resident">{% for r in rs %}<option value="{{r.id}}">{{r.year}} — {{r.surname}} {{r.firstname}}</option>{% endfor %}</select><label>{{t('terrain')}}</label><select name="terrain">{% for x in ts %}<option value="{{x.id}}">{{x.name}}</option>{% endfor %}</select><label>{{t('period')}}</label><select name="period">{% for x in ps %}<option value="{{x.id}}">{{x.name}}</option>{% endfor %}</select><button>{{t('check_save')}}</button></form></section><section><div class="wrap"><table><tr><th>{{t('period')}}</th><th>{{t('resident')}}</th><th>{{t('study_year')}}</th><th>{{t('terrain')}}</th><th>{{t('status')}}</th></tr>{% for a in rows %}<tr><td>{{a.period}}</td><td>{{a.surname}} {{a.firstname}}</td><td>{{a.year}}</td><td>{{a.terrain}}</td><td>{{t(a.status) if a.status in ['confirmed','pending','rejected'] else a.status}}</td></tr>{% endfor %}</table></div></section>""",rs=rs,ts=ts,ps=ps,rows=rows)
@app.route("/history",methods=["GET","POST"])
def history():
 if guard():return redirect("/login")
 c=db()
 if request.method=="POST":
  c.execute("INSERT INTO history(resident_id,terrain_id,year_label,period,date_done) VALUES(?,?,?,?,?)",(int(request.form["resident"]),int(request.form["terrain"]),request.form["year_label"],request.form.get("period",""),request.form.get("date_done",""))); c.commit(); flash(tr("done"))
 rs=c.execute("SELECT * FROM residents ORDER BY year DESC,surname").fetchall(); ts=c.execute("SELECT * FROM terrains ORDER BY CASE WHEN kind='optional' THEN 1 ELSE 0 END, name").fetchall(); rows=c.execute("SELECT h.*,r.surname,r.firstname,t.name terrain FROM history h JOIN residents r ON r.id=h.resident_id JOIN terrains t ON t.id=h.terrain_id ORDER BY h.id DESC").fetchall(); c.close()
 return page("""<section><h3>{{t('history_add')}}</h3><form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><label>{{t('resident')}}</label><select name="resident">{% for r in rs %}<option value="{{r.id}}">{{r.surname}} {{r.firstname}} — {{r.year}}</option>{% endfor %}</select><label>{{t('terrain')}}</label><select name="terrain">{% for x in ts %}<option value="{{x.id}}">{{x.name}}</option>{% endfor %}</select><label>{{t('academic_year')}}</label><input name="year_label" required placeholder="2025-2026"><label>{{t('period')}}</label><input name="period"><label>{{t('date')}}</label><input type="date" name="date_done"><button>{{t('save')}}</button></form></section><section><div class="wrap"><table><tr><th>{{t('resident')}}</th><th>{{t('terrain')}}</th><th>{{t('academic_year')}}</th><th>{{t('period')}}</th><th>{{t('date')}}</th></tr>{% for h in rows %}<tr><td>{{h.surname}} {{h.firstname}}</td><td>{{h.terrain}}</td><td>{{h.year_label}}</td><td>{{h.period}}</td><td>{{h.date_done}}</td></tr>{% endfor %}</table></div></section>""",rs=rs,ts=ts,rows=rows)
@app.get("/summary")
def summary():
 if guard():return redirect("/login")
 c=db(); y=setting(c,"year"); rs=c.execute("SELECT * FROM residents ORDER BY year DESC,surname").fetchall(); rows=[]
 for r in rs:
  a=c.execute("SELECT p.name period,t.name terrain,a.status FROM assignments a JOIN periods p ON p.id=a.period_id JOIN terrains t ON t.id=a.terrain_id WHERE a.resident_id=? AND p.year_label=? ORDER BY p.id",(r["id"],y)).fetchall()
  h=c.execute("SELECT t.name terrain,h.year_label,h.period,h.date_done FROM history h JOIN terrains t ON t.id=h.terrain_id WHERE h.resident_id=?",(r["id"],)).fetchall(); rows.append((r,a,h))
 c.close()
 return page("""<section><h3>{{t('summary')}} — {{year}}</h3><div class="wrap"><table><tr><th>{{t('resident')}}</th><th>{{t('study_year')}}</th><th>{{t('assign')}}</th><th>{{t('history')}}</th></tr>{% for r,a,h in rows %}<tr><td>{{r.surname}} {{r.firstname}}</td><td>{{r.year}}</td><td>{% for x in a %}<div>{{x.period}} — {{x.terrain}} ({{x.status}})</div>{% else %}—{% endfor %}</td><td>{% for x in h %}<div>{{x.terrain}} — {{x.year_label}} / {{x.period}} / {{x.date_done}}</div>{% else %}—{% endfor %}</td></tr>{% endfor %}</table></div></section>""",rows=rows,year=y)
@app.route("/decisions",methods=["GET","POST"])
def decisions():
 if guard():return redirect("/login")
 c=db()
 if request.method=="POST":
  aid=int(request.form["aid"]); outcome=request.form["outcome"]; reason=request.form.get("reason","").strip()
  a=c.execute("SELECT a.*,r.surname,r.firstname,t.name terrain,p.name period FROM assignments a JOIN residents r ON r.id=a.resident_id JOIN terrains t ON t.id=a.terrain_id JOIN periods p ON p.id=a.period_id WHERE a.id=? AND a.status='pending'",(aid,)).fetchone()
  if a and reason:
   if outcome=="approve":
    cap=c.execute("SELECT places FROM capacities WHERE year_label=? AND terrain_id=? AND period_id=?",(setting(c,"year"),a["terrain_id"],a["period_id"])).fetchone()
    used=c.execute("SELECT COUNT(*) FROM assignments WHERE terrain_id=? AND period_id=? AND status='confirmed'",(a["terrain_id"],a["period_id"])).fetchone()[0]
    dup=c.execute("SELECT id FROM assignments WHERE resident_id=? AND period_id=? AND id<>? AND status IN ('confirmed','pending')",(a["resident_id"],a["period_id"],aid)).fetchone()
    if not cap or used>=cap["places"] or dup: flash(tr("full") if not dup else tr("duplicate"))
    else:
     c.execute("UPDATE assignments SET status='confirmed' WHERE id=?",(aid,)); c.execute("INSERT INTO decisions(details,decision,reason,actor) VALUES(?,?,?,?)",(a["surname"]+" "+a["firstname"]+" — "+a["terrain"],tr("approve"),reason,session["user"])); c.commit(); flash(tr("done"))
   else:
    c.execute("UPDATE assignments SET status='rejected' WHERE id=?",(aid,)); c.execute("INSERT INTO decisions(details,decision,reason,actor) VALUES(?,?,?,?)",(a["surname"]+" "+a["firstname"]+" — "+a["terrain"],tr("reject"),reason,session["user"])); c.commit(); flash(tr("done"))
 pending=c.execute("SELECT a.id,r.surname,r.firstname,r.year,t.name terrain,p.name period FROM assignments a JOIN residents r ON r.id=a.resident_id JOIN terrains t ON t.id=a.terrain_id JOIN periods p ON p.id=a.period_id WHERE a.status='pending'").fetchall(); ds=c.execute("SELECT * FROM decisions ORDER BY id DESC").fetchall(); c.close()
 return page("""<section><h3>{{t('decisions')}}</h3>{% for a in pending %}<p><b>{{a.surname}} {{a.firstname}}</b> — {{a.terrain}} / {{a.period}}</p><form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><input type="hidden" name="aid" value="{{a.id}}"><input name="reason" placeholder="{{t('reason')}}" required><button name="outcome" value="approve">{{t('approve')}}</button> <button name="outcome" value="reject">{{t('reject')}}</button></form>{% else %}<p>{{t('none')}}</p>{% endfor %}</section><section><div class="wrap"><table><tr><th>Date</th><th>{{t('assign')}}</th><th>{{t('status')}}</th><th>{{t('reason')}}</th></tr>{% for d in ds %}<tr><td>{{d.created_at}}</td><td>{{d.details}}</td><td>{{d.decision}}</td><td>{{d.reason}}</td></tr>{% endfor %}</table></div></section>""",pending=pending,ds=ds)
@app.route("/settings",methods=["GET","POST"])
def settings():
 if guard():return redirect("/login")
 c=db()
 if request.method=="POST":
  lang=request.form.get("lang","ar")
  if lang in LANGS:session["lang"]=lang
  y=request.form.get("year","").strip()
  if y:
   c.execute("INSERT INTO settings(key,value) VALUES('year',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(y,))
   if not c.execute("SELECT 1 FROM periods WHERE year_label=?",(y,)).fetchone():
    for n in ["01 Fév - 30 Avr","01 Mai - 30 Juillet","01 Août - 30 Oct","01 Nov - 30 Jan"]:c.execute("INSERT OR IGNORE INTO periods(year_label,name) VALUES(?,?)",(y,n))
  d=request.form.get("director","").strip()
  if d:c.execute("INSERT INTO settings(key,value) VALUES('director',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(d,))
  pw=request.form.get("new_password","")
  if pw:c.execute("INSERT INTO settings(key,value) VALUES('password',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(generate_password_hash(pw),))
  c.commit(); flash(tr("done"))
 vals={r["key"]:r["value"] for r in c.execute("SELECT key,value FROM settings")}; c.close()
 return page("""<section><h3>{{t('settings')}}</h3><form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><label>{{t('language')}}</label><select name="lang"><option value="ar" {% if lang=='ar' %}selected{% endif %}>العربية</option><option value="fr" {% if lang=='fr' %}selected{% endif %}>Français</option><option value="en" {% if lang=='en' %}selected{% endif %}>English</option></select><label>{{t('year')}}</label><input name="year" value="{{vals.get('year','')}}" required><label>{{t('director')}}</label><input name="director" value="{{vals.get('director','')}}"><label>{{t('new_password')}}</label><input type="password" name="new_password"><button>{{t('change')}}</button></form><p class="muted">{{t('note')}}</p></section>""",vals=vals,lang=session.get("lang","ar"))
@app.get("/export")
def export():
 if guard():return redirect("/login")
 c=db(); out=io.StringIO(); w=csv.writer(out)
 for table in ["residents","terrains","periods","capacities","assignments","history","decisions"]:
  w.writerow([table])
  w.writerow([x[1] for x in c.execute('PRAGMA table_info("'+table+'")')])
  for row in c.execute('SELECT * FROM "'+table+'"'):w.writerow(list(row))
 c.close(); f=io.BytesIO(("\ufeff"+out.getvalue()).encode("utf-8")); return send_file(f,mimetype="text/csv",as_attachment=True,download_name="rotation_export.csv")
@app.get("/backup")
def backup():
 if guard():return redirect("/login")
 c=db(); c.execute("PRAGMA wal_checkpoint(FULL)"); c.close()
 target=os.path.join(BASE,"rotation_backup_download.db"); shutil.copy2(DB,target)
 return send_file(target,as_attachment=True,download_name="rotation_backup.db")
if __name__=="__main__":
 init(); app.run(host="127.0.0.1",port=int(os.environ.get("PORT","5000")),debug=False)
