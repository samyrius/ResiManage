# -*- coding: utf-8 -*-
from flask import Flask, request, redirect, session, render_template_string, flash, send_file
import sqlite3, os, hashlib, hmac, io, csv, shutil, secrets, zipfile
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

BASE=os.path.dirname(os.path.abspath(__file__))
DB=os.path.join(BASE,"rotation.db")
app=Flask(__name__)
app.secret_key=os.environ.get("ROTATION_SECRET") or secrets.token_hex(32)
UPLOAD_DIR=os.path.join(BASE,"uploads","residents")
app.config["MAX_CONTENT_LENGTH"]=5*1024*1024
app.config.update(
 SESSION_COOKIE_HTTPONLY=True,
 SESSION_COOKIE_SAMESITE="Lax",
 SESSION_COOKIE_SECURE=os.environ.get("ROTATION_COOKIE_SECURE")=="1",
)
LANGS=("ar","fr","en")
D={
"ar":{"app":"تسيير تربصات الأطباء المقيمين","home":"الرئيسية","residents":"المقيمون","photo":"صورة المقيم","photo_invalid":"ارفع صورة PNG أو JPG أو WEBP صالحة لا يتجاوز حجمها 5 ميغابايت.","photo_saved":"تم حفظ الصورة.","archived_at":"تاريخ الأرشفة","promotion_request_invalid":"اختر مقيمًا نشطًا في السنة الثانية أو الثالثة أو الرابعة.","promotion_pending_exists":"يوجد طلب ترقية معلّق لهذا المقيم.","promotion_vote_invalid":"تحقق من القرار والسبب.","promotions":"قرارات الترقية","dems_archive":"أرشيف الناجحين في DEMS","request_promotion":"طلب ترقية / قرار DEMS","promotion_vote":"تصويت المسؤول","promotion_waiting":"بانتظار موافقة المسؤولين الاثنين","promotion_rejected":"رُفض طلب الترقية","promotion_approved":"تمت الترقية بعد موافقة المسؤولين الاثنين","official_only":"التصويت مخصص لحسابي benhocine وdrdris فقط","notes":"ملاحظات","approve":"موافقة","reject":"رفض","username":"اسم المستخدم","users":"حسابات المسؤولين","display_name":"الاسم الكامل","role":"الصلاحية","super_admin":"مسؤول أعلى","operator":"مستخدم","create_user":"إنشاء حساب","user_invalid":"أدخل اسم مستخدم واسمًا وكلمة مرور من 12 حرفًا على الأقل وصلاحية صحيحة.","user_exists":"اسم المستخدم مستعمل من قبل.","profile":"الملف الشخصي","birth_place":"مكان الميلاد","birth_date":"تاريخ الميلاد","exams":"علامات الامتحانات","module":"المقياس","theory_score":"علامة النظري /20","practical_score":"علامة التطبيقي /20","add_exam":"إضافة علامة","advance":"ترقية إلى السنة التالية","advance_denied":"لا يمكن الترقية تلقائياً: تحقق من كل علامات السنة الأولى","advance_done":"تمت ترقية المقيم إلى السنة الثانية","exam_invalid":"تحقق من اسم المقياس والعلامات بين 0 و20.","required_modules":"مقاييس السنة الأولى المطلوبة (افصل بينها بفاصلة منقوطة)","modules_missing":"لم تُحدّد كل مقاييس السنة الأولى المطلوبة؛ لم تتم الترقية.","terrains":"المصالح","capacities":"المقاعد","assign":"التوزيع","history":"التاريخ","summary":"ملخص المقيمين","decisions":"القرارات","audit":"سجل التدقيق","settings":"الإعدادات","logout":"خروج","login":"دخول المسؤول","password":"كلمة المرور","setup_password":"أنشئ كلمة مرور للمسؤول (12 حرفًا على الأقل).","setup_password_error":"يجب أن تكون كلمة المرور 12 حرفًا على الأقل وأن يتطابق التأكيد.","weak_password":"كلمة المرور الجديدة يجب أن تكون 12 حرفًا على الأقل.","password_confirm":"تأكيد كلمة المرور","signin":"دخول","badpass":"كلمة المرور غير صحيحة","year":"السنة الجامعية","resident":"المقيم","surname":"اللقب","firstname":"الاسم","study_year":"السنة","phone":"الهاتف","repeat":"يعيد السنة","status":"الحالة","active":"نشط","inactive":"غير نشط","add":"إضافة","save":"حفظ","terrain":"المصلحة","kind":"النوع","mandatory":"إجباري","basic":"أساسي","optional":"اختياري","mandatory_year":"السنة الإلزامية","any":"حسب البرنامج","period":"الفترة","places":"عدد المقاعد","used":"المستعمل","remaining":"المتبقي","date":"تاريخ الإنجاز","academic_year":"السنة الجامعية","choose":"اختيار","assign_now":"تعيين مقيم","check_save":"التحقق والحفظ","confirmed":"مؤكد","pending":"بانتظار القرار","rejected":"مرفوض","history_add":"تسجيل تربص سابق","reason":"سبب القرار","approve":"موافقة","reject":"رفض","language":"لغة الواجهة","director":"المسؤول","new_password":"كلمة مرور جديدة (اختياري)","change":"حفظ الإعدادات","note":"تغيير اللغة لا يغيّر البيانات المحفوظة.","priority":"الأولوية للسنة الرابعة ثم الثالثة والثانية والأولى.","none":"لا توجد بيانات","capacity_first":"حدّد السعة أولاً لهذه المصلحة والفترة","full":"السعة مكتملة","duplicate":"المقيم مسجّل في نفس الفترة بمصلحة: ","same_terrain_year":"سبق للمقيم إنجاز هذه المصلحة خلال السنة الجامعية في الفترة: ","history_block":"التربص منجز سابقاً؛ يمنع التكرار حتى إكمال جميع المصالح.","history_repeat":"يمكن التكرار لأن المقيم أكمل جميع المصالح.","mismatch":"السنة لا تطابق السنة الإلزامية؛ التعيين بانتظار قرار المسؤول","done":"تم الحفظ","overview":"ملخص التوزيع السنوي","count":"عدد التعيينات","type":"التصنيف","export":"تصدير CSV","backup":"تنزيل نسخة احتياطية","all":"كل المصالح","four":"التعيينات المؤكدة / 4 فترات","waiting":"معلّق"},
"fr":{"app":"Gestion des stages des médecins résidents","home":"Accueil","residents":"Résidents","photo":"Photo du résident","photo_invalid":"Téléversez une image PNG, JPG ou WEBP valide de 5 Mo maximum.","photo_saved":"Photo enregistrée.","archived_at":"Date d’archivage","promotion_request_invalid":"Choisissez un résident actif de 2e, 3e ou 4e année.","promotion_pending_exists":"Une demande est déjà en attente pour ce résident.","promotion_vote_invalid":"Vérifiez la décision et le motif.","promotions":"Décisions de promotion","dems_archive":"Archives des lauréats DEMS","request_promotion":"Demander une promotion / décision DEMS","promotion_vote":"Vote du responsable","promotion_waiting":"En attente de l’approbation des deux responsables","promotion_rejected":"Demande de promotion refusée","promotion_approved":"Promotion validée par les deux responsables","official_only":"Le vote est réservé aux comptes benhocine et drdris","notes":"Notes","approve":"Approuver","reject":"Refuser","username":"Nom d’utilisateur","users":"Comptes administrateurs","display_name":"Nom complet","role":"Rôle","super_admin":"Super administrateur","operator":"Opérateur","create_user":"Créer le compte","user_invalid":"Saisissez un identifiant, un nom, un mot de passe de 12 caractères minimum et un rôle valide.","user_exists":"Ce nom d’utilisateur existe déjà.","profile":"Profil","birth_place":"Lieu de naissance","birth_date":"Date de naissance","exams":"Notes d’examen","module":"Module","theory_score":"Note théorique /20","practical_score":"Note pratique /20","add_exam":"Ajouter une note","advance":"Passer à l’année suivante","advance_denied":"Passage automatique refusé : vérifiez toutes les notes de première année","advance_done":"Résident promu en deuxième année","exam_invalid":"Vérifiez le module et les notes entre 0 et 20.","required_modules":"Modules requis de première année (séparés par des points-virgules)","modules_missing":"Tous les modules requis de première année ne sont pas définis ; promotion bloquée.","terrains":"Services","capacities":"Capacités","assign":"Affectations","history":"Historique","summary":"Bilan résidents","decisions":"Décisions","audit":"Journal d’audit","settings":"Paramètres","logout":"Déconnexion","login":"Connexion administrateur","password":"Mot de passe","setup_password":"Créez un mot de passe administrateur (12 caractères minimum).","setup_password_error":"Le mot de passe doit contenir au moins 12 caractères et les confirmations doivent correspondre.","weak_password":"Le nouveau mot de passe doit contenir au moins 12 caractères.","password_confirm":"Confirmer le mot de passe","signin":"Connexion","badpass":"Mot de passe incorrect","year":"Année universitaire","resident":"Résident","surname":"Nom","firstname":"Prénom","study_year":"Année","phone":"Téléphone","repeat":"Redouble","status":"Statut","active":"Actif","inactive":"Inactif","add":"Ajouter","save":"Enregistrer","terrain":"Service","kind":"Type","mandatory":"Obligatoire","basic":"De base","optional":"Optionnel","mandatory_year":"Année requise","any":"Selon le programme","period":"Période","places":"Nombre de places","used":"Utilisées","remaining":"Restantes","date":"Date de réalisation","academic_year":"Année universitaire","choose":"Choisir","assign_now":"Affecter un résident","check_save":"Vérifier et enregistrer","confirmed":"Confirmé","pending":"En attente","rejected":"Refusé","history_add":"Enregistrer un stage antérieur","reason":"Motif de décision","approve":"Approuver","reject":"Refuser","language":"Langue de l’interface","director":"Responsable","new_password":"Nouveau mot de passe (facultatif)","change":"Enregistrer les paramètres","note":"Changer de langue ne modifie pas les données.","priority":"Priorité aux 4e, puis 3e, 2e et 1re années.","none":"Aucune donnée","capacity_first":"Définissez d’abord la capacité du service et de la période","full":"Capacité complète","duplicate":"Résident déjà affecté pendant cette période au service : ","same_terrain_year":"Ce résident a déjà effectué ce service cette année, pendant la période : ","history_block":"Stage déjà effectué ; répétition bloquée avant d’avoir terminé tous les services.","history_repeat":"Répétition autorisée : tous les services ont été effectués.","mismatch":"Année différente de l’année requise ; décision du responsable nécessaire","done":"Enregistré","overview":"Vue annuelle des affectations","count":"Nombre d’affectations","type":"Catégorie","export":"Exporter CSV","backup":"Télécharger la sauvegarde","all":"Tous les services","four":"Affectations confirmées / 4 périodes","waiting":"En attente"},
"en":{"app":"Resident Rotation Manager","home":"Home","residents":"Residents","photo":"Resident photo","photo_invalid":"Upload a valid PNG, JPG, or WEBP image no larger than 5 MB.","photo_saved":"Photo saved.","archived_at":"Archived at","promotion_request_invalid":"Choose an active year 2, 3, or 4 resident.","promotion_pending_exists":"This resident already has a pending promotion request.","promotion_vote_invalid":"Check the decision and reason.","promotions":"Promotion decisions","dems_archive":"DEMS success archive","request_promotion":"Request promotion / DEMS decision","promotion_vote":"Administrator vote","promotion_waiting":"Waiting for both officials to approve","promotion_rejected":"Promotion request rejected","promotion_approved":"Promotion approved by both officials","official_only":"Voting is restricted to the benhocine and drdris accounts","notes":"Notes","approve":"Approve","reject":"Reject","username":"Username","users":"Administrator accounts","display_name":"Full name","role":"Role","super_admin":"Super administrator","operator":"Operator","create_user":"Create account","user_invalid":"Enter a username, name, password of at least 12 characters, and a valid role.","user_exists":"That username already exists.","profile":"Profile","birth_place":"Place of birth","birth_date":"Date of birth","exams":"Exam scores","module":"Module","theory_score":"Theory score /20","practical_score":"Practical score /20","add_exam":"Add score","advance":"Advance to next year","advance_denied":"Automatic advancement denied: check all first-year scores","advance_done":"Resident advanced to year two","exam_invalid":"Check the module and scores between 0 and 20.","required_modules":"Required first-year modules (semicolon-separated)","modules_missing":"Required first-year modules are not all configured; advancement blocked.","terrains":"Departments","capacities":"Capacity","assign":"Assignments","history":"History","summary":"Resident summary","decisions":"Decisions","audit":"Audit log","settings":"Settings","logout":"Log out","login":"Administrator login","password":"Password","setup_password":"Create an administrator password (at least 12 characters).","setup_password_error":"The password must be at least 12 characters and both entries must match.","weak_password":"The new password must contain at least 12 characters.","password_confirm":"Confirm password","signin":"Sign in","badpass":"Incorrect password","year":"Academic year","resident":"Resident","surname":"Surname","firstname":"First name","study_year":"Year","phone":"Phone","repeat":"Repeating year","status":"Status","active":"Active","inactive":"Inactive","add":"Add","save":"Save","terrain":"Department","kind":"Type","mandatory":"Mandatory","basic":"Core","optional":"Optional","mandatory_year":"Required year","any":"As per curriculum","period":"Period","places":"Places","used":"Used","remaining":"Remaining","date":"Completion date","academic_year":"Academic year","choose":"Choose","assign_now":"Assign resident","check_save":"Validate and save","confirmed":"Confirmed","pending":"Pending decision","rejected":"Rejected","history_add":"Record previous rotation","reason":"Decision reason","approve":"Approve","reject":"Reject","language":"Interface language","director":"Administrator","new_password":"New password (optional)","change":"Save settings","note":"Changing language does not change saved data.","priority":"Priority: year 4, then 3, 2 and 1.","none":"No data","capacity_first":"Set capacity for this department and period first","full":"Capacity is full","duplicate":"Resident already assigned during this period to: ","same_terrain_year":"This resident already completed this department this academic year, during: ","history_block":"Rotation completed previously; repeats blocked until all departments are completed.","history_repeat":"Repeat allowed because all departments have been completed.","mismatch":"Year does not match required year; administrator decision needed","done":"Saved","overview":"Annual assignment overview","count":"Assignment count","type":"Category","export":"Export CSV","backup":"Download backup","all":"All departments","four":"Confirmed assignments / 4 periods","waiting":"Pending"}
}
def tr(k): return D.get(session.get("lang","ar"),D["ar"]).get(k,D["ar"].get(k,k))
def db():
 c=sqlite3.connect(DB,timeout=20); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c
def setting(c,k,default=""):
 r=c.execute("SELECT value FROM settings WHERE key=?",(k,)).fetchone(); return r["value"] if r else default
def audit(c,action,details):
 actor=session.get("user","system")
 c.execute("INSERT INTO audit(action,details) VALUES(?,?)",(action,f"actor={actor}; {details}"))
def init():
 c=db()
 c.executescript("""
 CREATE TABLE IF NOT EXISTS residents(id INTEGER PRIMARY KEY,surname TEXT NOT NULL,firstname TEXT NOT NULL,year INTEGER NOT NULL CHECK(year BETWEEN 1 AND 4),phone TEXT DEFAULT '',repeat_year INTEGER DEFAULT 0,status TEXT DEFAULT 'active',birth_place TEXT DEFAULT '',birth_date TEXT DEFAULT '',photo_filename TEXT DEFAULT '');
 CREATE TABLE IF NOT EXISTS terrains(id INTEGER PRIMARY KEY,name TEXT UNIQUE NOT NULL,kind TEXT DEFAULT 'basic',mandatory_year INTEGER DEFAULT 0);
 CREATE TABLE IF NOT EXISTS periods(id INTEGER PRIMARY KEY,year_label TEXT NOT NULL,name TEXT NOT NULL,UNIQUE(year_label,name));
 CREATE TABLE IF NOT EXISTS capacities(id INTEGER PRIMARY KEY,year_label TEXT NOT NULL,terrain_id INTEGER,period_id INTEGER,places INTEGER NOT NULL,UNIQUE(year_label,terrain_id,period_id));
 CREATE TABLE IF NOT EXISTS assignments(id INTEGER PRIMARY KEY,resident_id INTEGER,terrain_id INTEGER,period_id INTEGER,status TEXT DEFAULT 'confirmed',UNIQUE(resident_id,period_id));
 CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY,resident_id INTEGER,terrain_id INTEGER,year_label TEXT,period TEXT,date_done TEXT);
 CREATE TABLE IF NOT EXISTS decisions(id INTEGER PRIMARY KEY,details TEXT,decision TEXT,reason TEXT,actor TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
 CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,action TEXT,details TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
 CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS resident_promotions(id INTEGER PRIMARY KEY,resident_id INTEGER NOT NULL,from_year INTEGER NOT NULL,to_year INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'pending',requested_by TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP,UNIQUE(resident_id,from_year,status),FOREIGN KEY(resident_id) REFERENCES residents(id));
 CREATE TABLE IF NOT EXISTS promotion_votes(id INTEGER PRIMARY KEY,promotion_id INTEGER NOT NULL,username TEXT NOT NULL,decision TEXT NOT NULL CHECK(decision IN ('approve','reject')),reason TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP,UNIQUE(promotion_id,username),FOREIGN KEY(promotion_id) REFERENCES resident_promotions(id));
 CREATE TABLE IF NOT EXISTS dems_archive(id INTEGER PRIMARY KEY,resident_id INTEGER UNIQUE NOT NULL,archived_at TEXT DEFAULT CURRENT_TIMESTAMP,approved_by TEXT NOT NULL,notes TEXT DEFAULT '',FOREIGN KEY(resident_id) REFERENCES residents(id));
 CREATE TABLE IF NOT EXISTS admins(id INTEGER PRIMARY KEY,username TEXT UNIQUE NOT NULL,display_name TEXT NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL CHECK(role IN ('super_admin','operator')),active INTEGER NOT NULL DEFAULT 1,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
 CREATE TABLE IF NOT EXISTS resident_exams(id INTEGER PRIMARY KEY,resident_id INTEGER NOT NULL,study_year INTEGER NOT NULL CHECK(study_year BETWEEN 1 AND 4),module TEXT NOT NULL,theory_score REAL NOT NULL CHECK(theory_score BETWEEN 0 AND 20),practical_score REAL NOT NULL CHECK(practical_score BETWEEN 0 AND 20),UNIQUE(resident_id,study_year,module),FOREIGN KEY(resident_id) REFERENCES residents(id) ON DELETE CASCADE);
 """)
 # Safe, additive migrations preserve existing resident and rotation data.
 resident_columns={row['name'] for row in c.execute('PRAGMA table_info(residents)')}
 for column in ('birth_place','birth_date','photo_filename'):
  if column not in resident_columns: c.execute(f'ALTER TABLE residents ADD COLUMN {column} TEXT DEFAULT \'\'')
 y=str(datetime.now().year)+"-"+str(datetime.now().year+1)
 c.execute("INSERT OR IGNORE INTO settings VALUES('year',?)",(y,))
 initial_password=os.environ.get("ROTATION_INITIAL_PASSWORD")
 if initial_password:
  c.execute("INSERT OR IGNORE INTO settings VALUES('password',?)",(generate_password_hash(initial_password),))
 # Preserve the existing single-admin credential by migrating it into an account.
 legacy_password=setting(c,'password')
 if legacy_password and not c.execute('SELECT 1 FROM admins LIMIT 1').fetchone():
  c.execute('INSERT INTO admins(username,display_name,password_hash,role) VALUES(?,?,?,?)',('admin','Administrateur initial',legacy_password,'super_admin'))
 c.execute("INSERT OR IGNORE INTO settings VALUES('director',?)",("Professor Benhocine",))
 for n,k in [("Réanimation chirurgicale","basic"),("Réanimation polyvalente","basic"),("Chirurgie générale","mandatory"),("Urologie","basic"),("Orthopédie","basic"),("Neurochirurgie","basic"),("Sédation","optional"),("Maxillo-faciale","optional"),("CCI","basic"),("Obstétrique","basic"),("Chirurgie cardiaque","optional"),("PU Médecine","basic"),("PU Chirurgie","basic"),("ORL","basic"),("Ophtalmologie","basic"),("Gynécologie","basic"),("Chirurgie thoracique","basic"),("Brûlés","optional"),("CAC DBK","optional")]:
  c.execute("INSERT OR IGNORE INTO terrains(name,kind) VALUES(?,?)",(n,k))
 c.execute("UPDATE terrains SET kind='optional' WHERE name IN ('Sédation','Maxillo-faciale','Chirurgie cardiaque','Brûlés','CAC DBK')")
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
 shell="""<!doctype html><html lang="{{lang}}" dir="{{'rtl' if lang=='ar' else 'ltr'}}"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{t('app')}}</title><style>body{font-family:Arial,sans-serif;background:#f1f5f9;margin:0;color:#182b3d}header{background:#164e83;color:white;padding:15px}main{max-width:1050px;margin:auto;padding:12px}nav{display:flex;gap:6px;overflow:auto;background:white;padding:10px}a,button{background:#164e83;color:white;padding:9px 12px;border:0;border-radius:7px;text-decoration:none;display:inline-block;white-space:nowrap}section{background:white;padding:13px;border:1px solid #d7e1eb;border-radius:10px;margin:10px 0}input,select{font:inherit;padding:9px;border:1px solid #bccada;border-radius:7px;width:100%;box-sizing:border-box;margin:4px 0 9px}label{display:block}table{border-collapse:collapse;width:100%;min-width:540px}td,th{text-align:start;border-bottom:1px solid #ddd;padding:8px}.wrap{overflow:auto}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px}.msg{background:#fff0c2;padding:10px;border-radius:7px}.good{color:green}.bad{color:#b21d1d}.muted{color:#526274}@media(max-width:600px){main{padding:7px}header{font-size:14px}}</style><header><h2>{{t('app')}}</h2>{{t('year')}}: {{year}}</header>{% if user %}<nav><a href="/">{{t('home')}}</a><a href="/residents">{{t('residents')}}</a><a href="/profiles">{{t('profile')}}</a><a href="/promotions">{{t('promotions')}}</a><a href="/dems-archive">{{t('dems_archive')}}</a><a href="/terrains">{{t('terrains')}}</a><a href="/capacities">{{t('capacities')}}</a><a href="/assign">{{t('assign')}}</a><a href="/history">{{t('history')}}</a><a href="/summary">{{t('summary')}}</a>{% if session.get('role')=='super_admin' %}<a href="/decisions">{{t('decisions')}}</a><a href="/users">{{t('users')}}</a><a href="/audit">{{t('audit')}}</a><a href="/settings">{{t('settings')}}</a><a href="/export">{{t('export')}}</a><a href="/backup">{{t('backup')}}</a>{% endif %}<a href="/logout">{{t('logout')}}</a></nav>{% endif %}<main>{% for m in get_flashed_messages() %}<p class="msg">{{m}}</p>{% endfor %}{{body|safe}}</main></html>"""
 context={"t":tr,"lang":lang,"year":setting(db(),"year")}
 context.update(kw)
 context.setdefault("csrf_token",session.setdefault("_csrf_token",secrets.token_urlsafe(32)))
 inner=render_template_string(body,**context)
 return render_template_string(shell,body=inner,lang=lang,t=tr,year=setting(db(),"year"),user=bool(session.get("user")))
def guard():
 if not session.get("user"): return redirect("/login")
def super_guard():
 if not session.get('user'): return redirect('/login')
 if session.get('role')!='super_admin': return 'Forbidden: super administrator permission required',403
@app.get("/lang/<lang>")
def lang(lang):
 if lang in LANGS: session["lang"]=lang
 return redirect(request.referrer or "/login")
@app.route("/login",methods=["GET","POST"])
def login():
 c=db()
 if request.method=="POST":
  submitted=request.form.get("password","")
  username=request.form.get("username","admin").strip().lower()
  account=c.execute("SELECT * FROM admins WHERE username=? AND active=1",(username,)).fetchone()
  if not c.execute("SELECT 1 FROM admins LIMIT 1").fetchone() and not setting(c,"password"):
   if len(submitted)<12 or submitted!=request.form.get("password_confirm","") or not username:
    flash(tr("setup_password_error"))
   else:
    hashed=generate_password_hash(submitted)
    c.execute("INSERT INTO settings(key,value) VALUES('password',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(hashed,))
    c.execute("INSERT INTO admins(username,display_name,password_hash,role) VALUES(?,?,?,?)",(username,request.form.get("display_name","Initial administrator").strip() or username,hashed,"super_admin"))
    c.commit(); c.close(); session.clear(); session["user"]=username; session["role"]="super_admin"; return redirect("/")
  elif account:
   p=account["password_hash"]; modern_hash=p.startswith(("scrypt:","pbkdf2:"))
   valid=check_password_hash(p,submitted) if modern_hash else hmac.compare_digest(hashlib.sha256(submitted.encode()).hexdigest(),p)
   if valid:
    if not modern_hash:
     upgraded=generate_password_hash(submitted)
     c.execute("UPDATE admins SET password_hash=? WHERE id=?",(upgraded,account["id"]))
     c.execute("UPDATE settings SET value=? WHERE key='password'",(upgraded,))
     c.commit()
    c.close(); session.clear(); session["user"]=username; session["role"]=account["role"]; return redirect("/")
   flash(tr("badpass"))
  else: flash(tr("badpass"))
 c.close()
 return page("""<section><p><a href="/lang/ar">العربية</a> <a href="/lang/fr">Français</a> <a href="/lang/en">English</a></p><h3>{{t('login')}}</h3>{% if not configured %}<p>{{t('setup_password')}}</p>{% endif %}<form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><label>{{t('username')}}</label><input name="username" value="admin" required><label>{{t('password')}}</label><input name="password" type="password" minlength="12" required>{% if not configured %}<label>{{t('password_confirm')}}</label><input name="password_confirm" type="password" minlength="12" required>{% endif %}<button>{{t('signin')}}</button></form></section>""",configured=bool(setting(db(),"password")))
@app.get("/logout")
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
  audit(c,"resident_update" if request.form.get("action")=="edit" else "resident_add",request.form.get("rid","") if request.form.get("action")=="edit" else (request.form.get("surname","").strip()+" "+request.form.get("firstname","").strip()))
  c.commit(); flash(tr("done"))
 rows=c.execute("SELECT * FROM residents ORDER BY status DESC,year DESC,surname").fetchall(); c.close()
 return page("""<section><h3>{{t('add')}} — {{t('resident')}}</h3><form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><div class="grid"><div><label>{{t('surname')}}</label><input name="surname" required></div><div><label>{{t('firstname')}}</label><input name="firstname" required></div><div><label>{{t('study_year')}}</label><select name="year">{% for y in range(1,5) %}<option>{{y}}</option>{% endfor %}</select></div><div><label>{{t('phone')}}</label><input name="phone"></div></div><label><input type="checkbox" name="repeat_year" value="1"> {{t('repeat')}}</label><button>{{t('add')}}</button></form></section><section><div class="wrap"><table><tr><th>{{t('resident')}}</th><th>{{t('study_year')}}</th><th>{{t('save')}}</th></tr>{% for r in rows %}<tr><td><a href="/profiles/{{r.id}}">{{r.surname}} {{r.firstname}}</a></td><td>{{r.year}}</td><td><form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><input type="hidden" name="action" value="edit"><input type="hidden" name="rid" value="{{r.id}}"><select name="year">{% for y in range(1,5) %}<option value="{{y}}" {% if r.year==y %}selected{% endif %}>{{y}}</option>{% endfor %}</select><label><input type="checkbox" name="repeat_year" value="1" {% if r.repeat_year %}checked{% endif %}> {{t('repeat')}}</label><select name="status"><option value="active">{{t('active')}}</option><option value="inactive">{{t('inactive')}}</option></select><button>{{t('save')}}</button></form></td></tr>{% endfor %}</table></div></section>""",rows=rows)
@app.route("/terrains",methods=["GET","POST"])
def terrains():
 if guard(): return redirect("/login")
 if request.method=="POST" and session.get("role")!="super_admin":return "Forbidden",403
 c=db()
 if request.method=="POST":
  try:
   name=request.form["name"].strip(); kind=request.form["kind"]
   c.execute("INSERT INTO terrains(name,kind,mandatory_year) VALUES(?,?,?)",(name,kind,int(request.form["mandatory_year"])))
   audit(c,"terrain_add",f"name={name};kind={kind}")
   c.commit(); flash(tr("done"))
  except sqlite3.IntegrityError: flash("Already exists / Existe déjà / المصلحة موجودة")
 rows=c.execute("SELECT * FROM terrains ORDER BY CASE WHEN kind='optional' THEN 1 ELSE 0 END, name").fetchall(); c.close()
 return page("""<section><h3>{{t('add')}} — {{t('terrain')}}</h3><form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><label>{{t('terrain')}}</label><input name="name" required><div class="grid"><div><label>{{t('kind')}}</label><select name="kind"><option value="mandatory">{{t('mandatory')}}</option><option value="basic">{{t('basic')}}</option><option value="optional">{{t('optional')}}</option></select></div><div><label>{{t('mandatory_year')}}</label><select name="mandatory_year"><option value="0">{{t('any')}}</option>{% for y in range(1,5) %}<option value="{{y}}">{{y}}</option>{% endfor %}</select></div></div><button>{{t('save')}}</button></form></section><section><div class="wrap"><table><tr><th>{{t('terrain')}}</th><th>{{t('kind')}}</th><th>{{t('mandatory_year')}}</th></tr>{% for r in rows %}<tr><td>{{r.name}}</td><td>{{t(r.kind)}}</td><td>{{r.mandatory_year or t('any')}}</td></tr>{% endfor %}</table></div></section>""",rows=rows)
@app.route("/capacities",methods=["GET","POST"])
def capacities():
 if guard(): return redirect("/login")
 if request.method=="POST" and session.get("role")!="super_admin":return "Forbidden",403
 c=db(); y=setting(c,"year")
 if request.method=="POST":
  tid,pid,places=int(request.form["terrain"]),int(request.form["period"]),max(0,int(request.form["places"]))
  used=c.execute("SELECT COUNT(*) FROM assignments WHERE terrain_id=? AND period_id=? AND status IN ('confirmed','pending')",(tid,pid)).fetchone()[0]
  if places<used: flash(tr("full"))
  else:
   c.execute("INSERT INTO capacities(year_label,terrain_id,period_id,places) VALUES(?,?,?,?) ON CONFLICT(year_label,terrain_id,period_id) DO UPDATE SET places=excluded.places",(y,tid,pid,places))
   audit(c,"capacity_update",f"year={y};terrain_id={tid};period_id={pid};places={places}")
   c.commit(); flash(tr("done"))
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
    elif old:
     c.execute("UPDATE assignments SET terrain_id=?,status=? WHERE id=?",(tid,status,old["id"]))
     audit(c,"assignment_reopened",f"assignment_id={old['id']};resident_id={rid};terrain_id={tid};period_id={pid};status={status}")
     c.commit(); flash(msg)
    else:
     c.execute("INSERT INTO assignments(resident_id,terrain_id,period_id,status) VALUES(?,?,?,?)",(rid,tid,pid,status))
     audit(c,"assignment_created",f"resident_id={rid};terrain_id={tid};period_id={pid};status={status}")
     c.commit(); flash(msg)
  except Exception: c.rollback(); flash("Invalid assignment / Affectation invalide / تعيين غير صالح")
 rs=c.execute("SELECT * FROM residents WHERE status='active' ORDER BY year DESC,surname").fetchall(); ts=c.execute("SELECT * FROM terrains ORDER BY CASE WHEN kind='optional' THEN 1 ELSE 0 END, name").fetchall(); ps=c.execute("SELECT * FROM periods WHERE year_label=? ORDER BY id",(y,)).fetchall()
 rows=c.execute("SELECT a.*,r.surname,r.firstname,r.year,t.name terrain,p.name period FROM assignments a JOIN residents r ON r.id=a.resident_id JOIN terrains t ON t.id=a.terrain_id JOIN periods p ON p.id=a.period_id WHERE p.year_label=? ORDER BY p.id,r.year DESC",(y,)).fetchall(); c.close()
 return page("""<section><h3>{{t('assign_now')}}</h3><p>{{t('priority')}}</p><form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><label>{{t('resident')}}</label><select name="resident">{% for r in rs %}<option value="{{r.id}}">{{r.year}} — {{r.surname}} {{r.firstname}}</option>{% endfor %}</select><label>{{t('terrain')}}</label><select name="terrain">{% for x in ts %}<option value="{{x.id}}">{{x.name}}</option>{% endfor %}</select><label>{{t('period')}}</label><select name="period">{% for x in ps %}<option value="{{x.id}}">{{x.name}}</option>{% endfor %}</select><button>{{t('check_save')}}</button></form></section><section><div class="wrap"><table><tr><th>{{t('period')}}</th><th>{{t('resident')}}</th><th>{{t('study_year')}}</th><th>{{t('terrain')}}</th><th>{{t('status')}}</th></tr>{% for a in rows %}<tr><td>{{a.period}}</td><td>{{a.surname}} {{a.firstname}}</td><td>{{a.year}}</td><td>{{a.terrain}}</td><td>{{t(a.status) if a.status in ['confirmed','pending','rejected'] else a.status}}</td></tr>{% endfor %}</table></div></section>""",rs=rs,ts=ts,ps=ps,rows=rows)
@app.route("/history",methods=["GET","POST"])
def history():
 if guard():return redirect("/login")
 c=db()
 if request.method=="POST":
  resident_id=int(request.form["resident"]); terrain_id=int(request.form["terrain"]); year_label=request.form["year_label"]
  c.execute("INSERT INTO history(resident_id,terrain_id,year_label,period,date_done) VALUES(?,?,?,?,?)",(resident_id,terrain_id,year_label,request.form.get("period",""),request.form.get("date_done","")))
  audit(c,"history_added",f"resident_id={resident_id};terrain_id={terrain_id};year={year_label}")
  c.commit(); flash(tr("done"))
 rs=c.execute("SELECT * FROM residents ORDER BY year DESC,surname").fetchall(); ts=c.execute("SELECT * FROM terrains ORDER BY CASE WHEN kind='optional' THEN 1 ELSE 0 END, name").fetchall(); rows=c.execute("SELECT h.*,r.surname,r.firstname,t.name terrain FROM history h JOIN residents r ON r.id=h.resident_id JOIN terrains t ON t.id=h.terrain_id ORDER BY h.id DESC").fetchall(); c.close()
 return page("""<section><h3>{{t('history_add')}}</h3><form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><label>{{t('resident')}}</label><select name="resident">{% for r in rs %}<option value="{{r.id}}">{{r.surname}} {{r.firstname}} — {{r.year}}</option>{% endfor %}</select><label>{{t('terrain')}}</label><select name="terrain">{% for x in ts %}<option value="{{x.id}}">{{x.name}}</option>{% endfor %}</select><label>{{t('academic_year')}}</label><input name="year_label" required placeholder="2025-2026"><label>{{t('period')}}</label><input name="period"><label>{{t('date')}}</label><input type="date" name="date_done"><button>{{t('save')}}</button></form></section><section><div class="wrap"><table><tr><th>{{t('resident')}}</th><th>{{t('terrain')}}</th><th>{{t('academic_year')}}</th><th>{{t('period')}}</th><th>{{t('date')}}</th></tr>{% for h in rows %}<tr><td>{{h.surname}} {{h.firstname}}</td><td>{{h.terrain}}</td><td>{{h.year_label}}</td><td>{{h.period}}</td><td>{{h.date_done}}</td></tr>{% endfor %}</table></div></section>""",rs=rs,ts=ts,rows=rows)
@app.get("/profiles")
def profiles():
 if guard():return redirect("/login")
 c=db(); rows=c.execute("SELECT id,surname,firstname,year,status,birth_place,birth_date FROM residents ORDER BY year DESC,surname,firstname").fetchall(); c.close()
 return page("""<section><h3>{{t('profile')}} — {{t('residents')}}</h3><div class="wrap"><table><tr><th>{{t('resident')}}</th><th>{{t('study_year')}}</th><th>{{t('birth_place')}}</th><th>{{t('birth_date')}}</th><th>{{t('status')}}</th></tr>{% for r in rows %}<tr><td><a href="/profiles/{{r.id}}">{{r.surname}} {{r.firstname}}</a></td><td>{{r.year}}</td><td>{{r.birth_place or '—'}}</td><td>{{r.birth_date or '—'}}</td><td>{{r.status}}</td></tr>{% else %}<tr><td colspan="5">{{t('none')}}</td></tr>{% endfor %}</table></div></section>""",rows=rows)

@app.get("/resident-photo/<int:resident_id>")
def resident_photo(resident_id):
 if guard():return redirect("/login")
 c=db(); row=c.execute("SELECT photo_filename FROM residents WHERE id=?",(resident_id,)).fetchone(); c.close()
 if not row or not row["photo_filename"]:return "Photo not found",404
 filename=os.path.basename(row["photo_filename"]); path=os.path.join(UPLOAD_DIR,filename)
 if not os.path.isfile(path):return "Photo not found",404
 return send_file(path,conditional=True)

@app.route("/profiles/<int:resident_id>",methods=["GET","POST"])
def resident_profile(resident_id):
 if guard():return redirect("/login")
 c=db(); resident=c.execute("SELECT * FROM residents WHERE id=?",(resident_id,)).fetchone()
 if not resident:c.close(); return "Resident not found",404
 if request.method=="POST":
  action=request.form.get("action","profile")
  if action=="profile":
   c.execute("UPDATE residents SET birth_place=?,birth_date=?,phone=? WHERE id=?",(request.form.get("birth_place","").strip(),request.form.get("birth_date",""),request.form.get("phone","").strip(),resident_id))
   audit(c,"resident_profile_updated",f"resident_id={resident_id}")
   c.commit(); flash(tr("done"))
  elif action=="photo":
   upload=request.files.get("photo")
   ext=os.path.splitext(upload.filename or "")[1].lower() if upload else ""
   header=upload.read(12) if upload else b""
   valid=(ext in (".jpg",".jpeg") and header.startswith(b"\xff\xd8\xff")) or (ext==".png" and header.startswith(b"\x89PNG\r\n\x1a\n")) or (ext==".webp" and header.startswith(b"RIFF") and header[8:12]==b"WEBP")
   if not upload or not valid:
    flash(tr("photo_invalid"))
   else:
    upload.seek(0); os.makedirs(UPLOAD_DIR,exist_ok=True); filename=secrets.token_hex(16)+ext
    upload.save(os.path.join(UPLOAD_DIR,filename))
    c.execute("UPDATE residents SET photo_filename=? WHERE id=?",(filename,resident_id))
    audit(c,"resident_photo_updated",f"resident_id={resident_id}")
    c.commit(); flash(tr("photo_saved"))
  elif action=="exam":
   try:
    study_year=int(request.form["study_year"]); module=request.form["module"].strip(); theory=float(request.form["theory_score"]); practical=float(request.form["practical_score"])
    if study_year not in (1,2,3,4) or not module or not (0<=theory<=20 and 0<=practical<=20): raise ValueError
    c.execute("INSERT INTO resident_exams(resident_id,study_year,module,theory_score,practical_score) VALUES(?,?,?,?,?) ON CONFLICT(resident_id,study_year,module) DO UPDATE SET theory_score=excluded.theory_score,practical_score=excluded.practical_score",(resident_id,study_year,module,theory,practical))
    audit(c,"resident_exam_saved",f"resident_id={resident_id};study_year={study_year};module={module};theory={theory};practical={practical}")
    c.commit(); flash(tr("done"))
   except (ValueError,sqlite3.IntegrityError): flash(tr("exam_invalid"))
  elif action=="advance":
   required=[m.strip() for m in setting(c,"year1_required_modules").split(";") if m.strip()]
   marks=c.execute("SELECT module,theory_score,practical_score FROM resident_exams WHERE resident_id=? AND study_year=1",(resident_id,)).fetchall()
   by_module={x["module"]:x for x in marks}
   complete=bool(required) and all(m in by_module for m in required)
   required_marks=[by_module[m] for m in required if m in by_module]
   if resident["year"]==1 and complete and required_marks and all(x["theory_score"]>=10 and x["practical_score"]>=10 for x in required_marks) and sum((x["theory_score"]+x["practical_score"])/2 for x in required_marks)/len(required_marks)>=10:
    c.execute("UPDATE residents SET year=2,repeat_year=0 WHERE id=?",(resident_id,)); audit(c,"resident_advanced_year_1",f"resident_id={resident_id};modules={len(marks)}"); c.commit(); flash(tr("advance_done"))
   else: flash(tr("advance_denied") if required else tr("modules_missing"))
  resident=c.execute("SELECT * FROM residents WHERE id=?",(resident_id,)).fetchone()
 exams=c.execute("SELECT * FROM resident_exams WHERE resident_id=? ORDER BY study_year,module",(resident_id,)).fetchall()
 stages=c.execute("SELECT h.year_label,h.period,h.date_done,t.name terrain,'history' source FROM history h JOIN terrains t ON t.id=h.terrain_id WHERE h.resident_id=? UNION ALL SELECT p.year_label,p.name,a.status||' assignment',t.name,'assignment' FROM assignments a JOIN periods p ON p.id=a.period_id JOIN terrains t ON t.id=a.terrain_id WHERE a.resident_id=? ORDER BY 1,2",(resident_id,resident_id)).fetchall()
 c.close()
 return page("""<section><h3>{{t('profile')}}: {{resident.surname}} {{resident.firstname}}</h3>{% if resident.photo_filename %}<img src="/resident-photo/{{resident.id}}" alt="{{t('photo')}}" style="max-width:180px;max-height:220px;border-radius:8px">{% endif %}<p>{{t('study_year')}}: {{resident.year}} · {{t('phone')}}: {{resident.phone or '—'}}</p><form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><input type="hidden" name="action" value="profile"><label>{{t('birth_place')}}</label><input name="birth_place" value="{{resident.birth_place or ''}}"><label>{{t('birth_date')}}</label><input type="date" name="birth_date" value="{{resident.birth_date or ''}}"><label>{{t('phone')}}</label><input name="phone" value="{{resident.phone or ''}}"><button>{{t('save')}}</button></form><form method="post" enctype="multipart/form-data"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><input type="hidden" name="action" value="photo"><label>{{t('photo')}}</label><input type="file" name="photo" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" required><button>{{t('photo')}}</button></form></section><section><h3>{{t('exams')}}</h3><form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><input type="hidden" name="action" value="exam"><label>{{t('study_year')}}</label><select name="study_year">{% for y in range(1,5) %}<option value="{{y}}">{{y}}</option>{% endfor %}</select><label>{{t('module')}}</label><input name="module" required><div class="grid"><div><label>{{t('theory_score')}}</label><input type="number" name="theory_score" min="0" max="20" step="0.01" required></div><div><label>{{t('practical_score')}}</label><input type="number" name="practical_score" min="0" max="20" step="0.01" required></div></div><button>{{t('add_exam')}}</button></form><div class="wrap"><table><tr><th>{{t('study_year')}}</th><th>{{t('module')}}</th><th>{{t('theory_score')}}</th><th>{{t('practical_score')}}</th><th>Moyenne</th></tr>{% for e in exams %}<tr><td>{{e.study_year}}</td><td>{{e.module}}</td><td>{{e.theory_score}}</td><td>{{e.practical_score}}</td><td>{{'%.2f'|format((e.theory_score+e.practical_score)/2)}}</td></tr>{% else %}<tr><td colspan="5">{{t('none')}}</td></tr>{% endfor %}</table></div>{% if resident.year==1 %}<form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><input type="hidden" name="action" value="advance"><button>{{t('advance')}}</button></form>{% endif %}</section><section><h3>{{t('history')}}</h3><div class="wrap"><table><tr><th>{{t('academic_year')}}</th><th>{{t('period')}}</th><th>{{t('terrain')}}</th><th>{{t('status')}}</th></tr>{% for st in stages %}<tr><td>{{st.year_label}}</td><td>{{st.period}}</td><td>{{st.terrain}}</td><td>{{st.source}}</td></tr>{% else %}<tr><td colspan="4">{{t('none')}}</td></tr>{% endfor %}</table></div></section>""",resident=resident,exams=exams,stages=stages)

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
 if session.get("role")!="super_admin":return "Forbidden",403
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
     c.execute("UPDATE assignments SET status='confirmed' WHERE id=?",(aid,)); c.execute("INSERT INTO decisions(details,decision,reason,actor) VALUES(?,?,?,?)",(a["surname"]+" "+a["firstname"]+" — "+a["terrain"],tr("approve"),reason,session["user"]))
     audit(c,"assignment_approved",f"assignment_id={aid};reason={reason}")
     c.commit(); flash(tr("done"))
   else:
    c.execute("UPDATE assignments SET status='rejected' WHERE id=?",(aid,)); c.execute("INSERT INTO decisions(details,decision,reason,actor) VALUES(?,?,?,?)",(a["surname"]+" "+a["firstname"]+" — "+a["terrain"],tr("reject"),reason,session["user"]))
    audit(c,"assignment_rejected",f"assignment_id={aid};reason={reason}")
    c.commit(); flash(tr("done"))
 pending=c.execute("SELECT a.id,r.surname,r.firstname,r.year,t.name terrain,p.name period FROM assignments a JOIN residents r ON r.id=a.resident_id JOIN terrains t ON t.id=a.terrain_id JOIN periods p ON p.id=a.period_id WHERE a.status='pending'").fetchall(); ds=c.execute("SELECT * FROM decisions ORDER BY id DESC").fetchall(); c.close()
 return page("""<section><h3>{{t('decisions')}}</h3>{% for a in pending %}<p><b>{{a.surname}} {{a.firstname}}</b> — {{a.terrain}} / {{a.period}}</p><form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><input type="hidden" name="aid" value="{{a.id}}"><input name="reason" placeholder="{{t('reason')}}" required><button name="outcome" value="approve">{{t('approve')}}</button> <button name="outcome" value="reject">{{t('reject')}}</button></form>{% else %}<p>{{t('none')}}</p>{% endfor %}</section><section><div class="wrap"><table><tr><th>Date</th><th>{{t('assign')}}</th><th>{{t('status')}}</th><th>{{t('reason')}}</th></tr>{% for d in ds %}<tr><td>{{d.created_at}}</td><td>{{d.details}}</td><td>{{d.decision}}</td><td>{{d.reason}}</td></tr>{% endfor %}</table></div></section>""",pending=pending,ds=ds)
@app.route("/settings",methods=["GET","POST"])
def settings():
 if guard():return redirect("/login")
 if session.get("role")!="super_admin":return "Forbidden",403
 c=db()
 if request.method=="POST":
  lang=request.form.get("lang","ar")
  if lang in LANGS:session["lang"]=lang
  y=request.form.get("year","").strip()
  if y:
   c.execute("INSERT INTO settings(key,value) VALUES('year',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(y,))
   if not c.execute("SELECT 1 FROM periods WHERE year_label=?",(y,)).fetchone():
    for n in ["01 Fév - 30 Avr","01 Mai - 30 Juillet","01 Août - 30 Oct","01 Nov - 30 Jan"]:c.execute("INSERT OR IGNORE INTO periods(year_label,name) VALUES(?,?)",(y,n))
  required_modules=request.form.get("year1_required_modules","").strip()
  c.execute("INSERT INTO settings(key,value) VALUES('year1_required_modules',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(required_modules,))
  d=request.form.get("director","").strip()
  if d:c.execute("INSERT INTO settings(key,value) VALUES('director',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(d,))
  pw=request.form.get("new_password","")
  if pw and len(pw)<12:flash(tr("weak_password"))
  elif pw:
   hashed=generate_password_hash(pw)
   c.execute("INSERT INTO settings(key,value) VALUES('password',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(hashed,))
   c.execute("UPDATE admins SET password_hash=? WHERE username=?",(hashed,session["user"]))
  audit(c,"settings_updated",f"year={y};director_changed={bool(d)}")
  if pw and len(pw)>=12:audit(c,"password_changed","administrator password updated")
  c.commit(); flash(tr("done"))
 vals={r["key"]:r["value"] for r in c.execute("SELECT key,value FROM settings")}; c.close()
 return page("""<section><h3>{{t('settings')}}</h3><form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><label>{{t('language')}}</label><select name="lang"><option value="ar" {% if lang=='ar' %}selected{% endif %}>العربية</option><option value="fr" {% if lang=='fr' %}selected{% endif %}>Français</option><option value="en" {% if lang=='en' %}selected{% endif %}>English</option></select><label>{{t('year')}}</label><input name="year" value="{{vals.get('year','')}}" required><label>{{t('director')}}</label><input name="director" value="{{vals.get('director','')}}"><label>{{t('required_modules')}}</label><input name="year1_required_modules" value="{{vals.get('year1_required_modules','')}}" placeholder="Module A;Module B;Module C"><label>{{t('new_password')}}</label><input type="password" name="new_password"><button>{{t('change')}}</button></form><p class="muted">{{t('note')}}</p></section>""",vals=vals,lang=session.get("lang","ar"))
@app.route("/promotions",methods=["GET","POST"])
def promotions():
 if guard():return redirect("/login")
 if session.get("role")!="super_admin":return "Forbidden",403
 c=db()
 if request.method=="POST":
  action=request.form.get("action","request")
  if action=="request":
   try: resident_id=int(request.form.get("resident","0"))
   except ValueError: resident_id=0
   resident=c.execute("SELECT * FROM residents WHERE id=? AND status='active'",(resident_id,)).fetchone()
   if not resident or resident["year"] not in (2,3,4):
    flash(tr("promotion_request_invalid"))
   elif c.execute("SELECT 1 FROM resident_promotions WHERE resident_id=? AND from_year=? AND status='pending'",(resident_id,resident["year"])).fetchone():
    flash(tr("promotion_pending_exists"))
   else:
    target=resident["year"]+1
    c.execute("INSERT INTO resident_promotions(resident_id,from_year,to_year,status,requested_by) VALUES(?,?,?,'pending',?)",(resident_id,resident["year"],target,session["user"]))
    promotion_id=c.execute("SELECT last_insert_rowid()").fetchone()[0]
    audit(c,"promotion_requested",f"promotion_id={promotion_id};resident_id={resident_id};from={resident['year']};to={target}")
    c.commit(); flash(tr("done"))
  elif action=="vote":
   username=session.get("user","")
   if username not in ("benhocine","drdris"):
    flash(tr("official_only"))
   else:
    try: promotion_id=int(request.form.get("promotion_id","0"))
    except ValueError: promotion_id=0
    decision=request.form.get("decision","")
    reason=request.form.get("reason","").strip()
    promotion=c.execute("SELECT * FROM resident_promotions WHERE id=? AND status='pending'",(promotion_id,)).fetchone()
    if not promotion or decision not in ("approve","reject") or not reason:
     flash(tr("promotion_vote_invalid"))
    else:
     c.execute("INSERT INTO promotion_votes(promotion_id,username,decision,reason) VALUES(?,?,?,?) ON CONFLICT(promotion_id,username) DO UPDATE SET decision=excluded.decision,reason=excluded.reason,created_at=CURRENT_TIMESTAMP",(promotion_id,username,decision,reason))
     votes=c.execute("SELECT username,decision FROM promotion_votes WHERE promotion_id=?",(promotion_id,)).fetchall()
     votes_by_user={v["username"]:v["decision"] for v in votes}
     if "reject" in votes_by_user.values():
      c.execute("UPDATE resident_promotions SET status='rejected' WHERE id=?",(promotion_id,))
      audit(c,"promotion_rejected",f"promotion_id={promotion_id};voter={username};reason={reason}")
      flash(tr("promotion_rejected"))
     elif votes_by_user.get("benhocine")=="approve" and votes_by_user.get("drdris")=="approve":
      c.execute("UPDATE resident_promotions SET status='approved' WHERE id=?",(promotion_id,))
      resident=c.execute("SELECT * FROM residents WHERE id=?",(promotion["resident_id"],)).fetchone()
      if promotion["to_year"]==5:
       c.execute("INSERT OR IGNORE INTO dems_archive(resident_id,approved_by,notes) VALUES(?,?,?)",(resident["id"],"benhocine,drdris","DEMS réussi — validation des deux responsables"))
       c.execute("UPDATE residents SET status='dems_success' WHERE id=?",(resident["id"],))
       audit(c,"dems_success_archived",f"resident_id={resident['id']};promotion_id={promotion_id}")
      else:
       c.execute("UPDATE residents SET year=?,repeat_year=0 WHERE id=?",(promotion["to_year"],resident["id"]))
       audit(c,"resident_advanced_by_officials",f"resident_id={resident['id']};from={promotion['from_year']};to={promotion['to_year']}")
      flash(tr("promotion_approved"))
     else:
      audit(c,"promotion_vote_recorded",f"promotion_id={promotion_id};voter={username};decision={decision}")
      flash(tr("promotion_waiting"))
     c.commit()
 residents=c.execute("SELECT id,surname,firstname,year FROM residents WHERE status='active' AND year BETWEEN 2 AND 4 ORDER BY year DESC,surname").fetchall()
 rows=c.execute("SELECT p.*,r.surname,r.firstname,r.year FROM resident_promotions p JOIN residents r ON r.id=p.resident_id ORDER BY CASE p.status WHEN 'pending' THEN 0 ELSE 1 END,p.id DESC").fetchall()
 votes={r["id"]:c.execute("SELECT username,decision,reason,created_at FROM promotion_votes WHERE promotion_id=? ORDER BY username",(r["id"],)).fetchall() for r in rows}
 c.close()
 return page("""<section><h3>{{t('request_promotion')}}</h3><p>{{t('official_only')}}. Les années 2–4 exigent deux approbations distinctes; l’année 4 mène à l’archive DEMS.</p><form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><input type="hidden" name="action" value="request"><label>{{t('resident')}}</label><select name="resident" required>{% for r in residents %}<option value="{{r.id}}">{{r.year}} — {{r.surname}} {{r.firstname}}</option>{% endfor %}</select><button>{{t('request_promotion')}}</button></form></section><section><h3>{{t('promotions')}}</h3><div class="wrap"><table><tr><th>{{t('resident')}}</th><th>{{t('study_year')}}</th><th>{{t('status')}}</th><th>{{t('promotion_vote')}}</th></tr>{% for p in rows %}<tr><td>{{p.surname}} {{p.firstname}}</td><td>{{p.from_year}} → {{'DEMS' if p.to_year==5 else p.to_year}}</td><td>{{p.status}}</td><td>{% for v in votes[p.id] %}<div>{{v.username}}: {{v.decision}} — {{v.reason}}</div>{% endfor %}{% if p.status=='pending' and session.get('user') in ['benhocine','drdris'] %}<form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><input type="hidden" name="action" value="vote"><input type="hidden" name="promotion_id" value="{{p.id}}"><input name="reason" placeholder="{{t('reason')}}" required><button name="decision" value="approve">{{t('approve')}}</button><button name="decision" value="reject">{{t('reject')}}</button></form>{% endif %}</td></tr>{% else %}<tr><td colspan="4">{{t('none')}}</td></tr>{% endfor %}</table></div></section>""",residents=residents,rows=rows,votes=votes)

@app.get("/dems-archive")
def dems_archive():
 if guard():return redirect("/login")
 if session.get("role")!="super_admin":return "Forbidden",403
 c=db()
 rows=c.execute("SELECT a.archived_at,a.approved_by,a.notes,r.id,r.surname,r.firstname,r.year,r.birth_place,r.birth_date,(SELECT COUNT(*) FROM history h WHERE h.resident_id=r.id)+(SELECT COUNT(*) FROM assignments x WHERE x.resident_id=r.id) AS stage_count FROM dems_archive a JOIN residents r ON r.id=a.resident_id ORDER BY a.archived_at DESC").fetchall()
 c.close()
 return page("""<section><h3>{{t('dems_archive')}}</h3><p>Les dossiers et historiques sont conservés; aucun résident n’est supprimé.</p><div class="wrap"><table><tr><th>{{t('resident')}}</th><th>{{t('study_year')}}</th><th>{{t('birth_place')}}</th><th>{{t('archived_at')}}</th><th>{{t('history')}}</th><th>{{t('notes')}}</th></tr>{% for r in rows %}<tr><td><a href="/profiles/{{r.id}}">{{r.surname}} {{r.firstname}}</a></td><td>{{r.year}}</td><td>{{r.birth_place or '—'}}</td><td>{{r.archived_at}}</td><td>{{r.stage_count}}</td><td>{{r.notes}}</td></tr>{% else %}<tr><td colspan="6">{{t('none')}}</td></tr>{% endfor %}</table></div></section>""",rows=rows)

@app.route("/users",methods=["GET","POST"])
def users():
 if guard():return redirect("/login")
 if session.get("role")!="super_admin":return "Forbidden",403
 c=db()
 if request.method=="POST":
  username=request.form.get("username","").strip().lower(); display_name=request.form.get("display_name","").strip(); password=request.form.get("password",""); role=request.form.get("role","operator")
  if not username or not display_name or len(password)<12 or role not in ("super_admin","operator"):
   flash(tr("user_invalid"))
  else:
   try:
    c.execute("INSERT INTO admins(username,display_name,password_hash,role) VALUES(?,?,?,?)",(username,display_name,generate_password_hash(password),role))
    audit(c,"admin_account_created",f"username={username};role={role}")
    c.commit(); flash(tr("done"))
   except sqlite3.IntegrityError:flash(tr("user_exists"))
 rows=c.execute("SELECT id,username,display_name,role,active,created_at FROM admins ORDER BY id").fetchall(); c.close()
 return page("""<section><h3>{{t('users')}}</h3><form method="post"><input type="hidden" name="_csrf_token" value="{{csrf_token}}"><label>{{t('username')}}</label><input name="username" required pattern="[A-Za-z0-9_.-]{3,40}"><label>{{t('display_name')}}</label><input name="display_name" required><label>{{t('password')}}</label><input type="password" name="password" minlength="12" required><label>{{t('role')}}</label><select name="role"><option value="super_admin">{{t('super_admin')}}</option><option value="operator">{{t('operator')}}</option></select><button>{{t('create_user')}}</button></form></section><section><div class="wrap"><table><tr><th>{{t('username')}}</th><th>{{t('display_name')}}</th><th>{{t('role')}}</th><th>{{t('status')}}</th></tr>{% for u in rows %}<tr><td>{{u.username}}</td><td>{{u.display_name}}</td><td>{{t(u.role)}}</td><td>{{t('active') if u.active else t('inactive')}}</td></tr>{% endfor %}</table></div></section>""",rows=rows)

@app.get("/audit")
def audit_log():
 if guard():return redirect("/login")
 if session.get("role")!="super_admin":return "Forbidden",403
 c=db(); rows=c.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 200").fetchall(); c.close()
 return page("""<section><h3>{{t('audit')}}</h3><div class="wrap"><table><tr><th>ID</th><th>Action</th><th>Details</th><th>Date</th></tr>{% for r in rows %}<tr><td>{{r.id}}</td><td>{{r.action}}</td><td>{{r.details}}</td><td>{{r.created_at}}</td></tr>{% else %}<tr><td colspan="4">{{t('none')}}</td></tr>{% endfor %}</table></div></section>""",rows=rows)
@app.get("/export")
def export():
 if guard():return redirect("/login")
 if session.get("role")!="super_admin":return "Forbidden",403
 c=db(); out=io.StringIO(); w=csv.writer(out)
 for table in ["residents","terrains","periods","capacities","assignments","history","decisions","audit"]:
  w.writerow([table])
  w.writerow([x[1] for x in c.execute('PRAGMA table_info("'+table+'")')])
  for row in c.execute('SELECT * FROM "'+table+'"'):w.writerow(list(row))
 c.close(); f=io.BytesIO(("\ufeff"+out.getvalue()).encode("utf-8")); return send_file(f,mimetype="text/csv",as_attachment=True,download_name="rotation_export.csv")
@app.get("/backup")
def backup():
 if guard():return redirect("/login")
 if session.get("role")!="super_admin":return "Forbidden",403
 c=db(); c.execute("PRAGMA wal_checkpoint(FULL)"); c.close()
 target=os.path.join(BASE,"rotation_backup_download.zip")
 with zipfile.ZipFile(target,"w",compression=zipfile.ZIP_DEFLATED) as archive:
  archive.write(DB,"rotation.db")
  if os.path.isdir(UPLOAD_DIR):
   for root,_,files in os.walk(UPLOAD_DIR):
    for name in files:
     full=os.path.join(root,name); archive.write(full,os.path.relpath(full,BASE))
 return send_file(target,as_attachment=True,download_name="rotation_backup.zip")
if __name__=="__main__":
 init(); app.run(host="127.0.0.1",port=int(os.environ.get("PORT","5000")),debug=False)
