# -*- coding: utf-8 -*-
from flask import Flask, request, redirect, session, render_template_string, flash, send_file, send_from_directory
import sqlite3, os, hashlib, hmac, io, csv, shutil, json, tempfile, re, subprocess, secrets
from datetime import datetime
from werkzeug.utils import secure_filename

BASE=os.path.dirname(os.path.abspath(__file__))
DB=os.path.join(BASE,"rotation.db")
def local_secret_key():
 path=os.path.join(BASE,".rotation_secret")
 try:
  with open(path,"r",encoding="ascii") as handle: return handle.read().strip()
 except FileNotFoundError:
  value=secrets.token_hex(32)
  try:
   fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
   with os.fdopen(fd,"w",encoding="ascii") as handle: handle.write(value)
   return value
  except FileExistsError:
   with open(path,"r",encoding="ascii") as handle: return handle.read().strip()
app=Flask(__name__)
app.config["MAX_CONTENT_LENGTH"]=25*1024*1024
app.secret_key=os.environ.get("ROTATION_SECRET") or local_secret_key()
LANGS=("ar","fr","en")
D={
"ar":{"app":"ResiTrack","home":"الرئيسية","residents":"المقيمون","manage_residents":"إضافة وإدارة المقيمين","import_residents":"استيراد المقيمين","promotion":"قرارات الترقية والامتحانات","dems_success":"قائمة الناجحين في DEMS","settings_page":"إعدادات التطبيق","terrains":"المصالح","capacities":"المقاعد","assign":"التوزيع","history":"التاريخ","summary":"ملخص المقيمين","decisions":"القرارات","settings":"الإعدادات","logout":"خروج","login":"دخول المسؤول","password":"كلمة المرور","signin":"دخول","badpass":"كلمة المرور غير صحيحة","year":"السنة الجامعية","resident":"المقيم","surname":"اللقب","firstname":"الاسم","study_year":"السنة","phone":"الهاتف","repeat":"يعيد السنة","status":"الحالة","active":"نشط","inactive":"غير نشط","add":"إضافة","save":"حفظ","terrain":"المصلحة","kind":"النوع","mandatory":"إجباري","basic":"أساسي","optional":"اختياري","mandatory_year":"السنة الإلزامية","any":"حسب البرنامج","period":"الفترة","places":"عدد المقاعد","used":"المستعمل","remaining":"المتبقي","date":"تاريخ الإنجاز","academic_year":"السنة الجامعية","choose":"اختيار","assign_now":"تعيين مقيم","check_save":"التحقق والحفظ","confirmed":"مؤكد","pending":"بانتظار القرار","rejected":"مرفوض","history_add":"تسجيل تربص سابق","reason":"سبب القرار","approve":"موافقة","reject":"رفض","language":"لغة الواجهة","director":"المسؤول","new_password":"كلمة مرور جديدة (اختياري)","change":"حفظ الإعدادات","note":"تغيير اللغة لا يغيّر البيانات المحفوظة.","priority":"الأولوية للسنة الرابعة ثم الثالثة والثانية والأولى.","none":"لا توجد بيانات","capacity_first":"حدّد السعة أولاً لهذه المصلحة والفترة","full":"السعة مكتملة","duplicate":"المقيم مسجّل في نفس الفترة بمصلحة: ","same_terrain_year":"سبق للمقيم إنجاز هذه المصلحة خلال السنة الجامعية في الفترة: ","history_block":"التربص منجز سابقاً؛ يمنع التكرار حتى إكمال جميع المصالح.","history_repeat":"يمكن التكرار لأن المقيم أكمل جميع المصالح.","mismatch":"السنة لا تطابق السنة الإلزامية؛ التعيين بانتظار قرار المسؤول","done":"تم الحفظ","overview":"ملخص التوزيع السنوي","count":"عدد التعيينات","type":"التصنيف" ,"export":"تصدير CSV","backup":"تنزيل نسخة احتياطية","all":"كل المصالح","four":"التعيينات المؤكدة / 4 فترات","waiting":"معلّق","users":"المستخدمون","import":"استيراد","objectives":"الأهداف","exams":"الامتحانات","dems":"أرشيف DEMS","audit":"سجل التدقيق","restore":"استرجاع","username":"اسم المستخدم","role":"الصلاحية","standard_user":"مستخدم عادي","super_admin":"مسؤول عام","created":"تاريخ الإنشاء","active_col":"نشط","actor":"الفاعل","action":"الإجراء","details":"التفاصيل","module":"المادة","theory":"نظري","practical":"تطبيقي","success_date":"تاريخ النجاح","file":"الملف","objective":"الهدف","archive":"أرشفة","users_help":"أنشئ حسابًا مستقلًا لكل مسؤول، وامنح الأستاذ Benhocine والدكتور Dris صلاحية المسؤول العام.","import_help":"ارفع ملفًا يحتوي على اللقب والاسم والسنة الدراسية. راجع المعاينة قبل التأكيد؛ لن تُختلق أي تربصات سابقة.","restore_help":"سيتم التحقق من سلامة قاعدة البيانات وإنشاء نسخة احتياطية من القاعدة الحالية قبل الاسترجاع.","confirm_password":"تأكيد كلمة المرور","confirm_import":"تأكيد الاستيراد","cancel":"إلغاء","upload_preview":"رفع ومعاينة","archive_note":"تُحفظ بيانات المقيم وتاريخه ولا تُحذف."},
"fr":{"app":"ResiTrack","home":"Accueil","residents":"Résidents","manage_residents":"Gérer les résidents","import_residents":"Importer les résidents","promotion":"Décisions de promotion et examens","dems_success":"Lauréats du DEMS","settings_page":"Paramètres de l’application","terrains":"Services","capacities":"Capacités","assign":"Affectations","history":"Historique","summary":"Bilan résidents","decisions":"Décisions","settings":"Paramètres","logout":"Déconnexion","login":"Connexion administrateur","password":"Mot de passe","signin":"Connexion","badpass":"Mot de passe incorrect","year":"Année universitaire","resident":"Résident","surname":"Nom","firstname":"Prénom","study_year":"Année","phone":"Téléphone","repeat":"Redouble","status":"Statut","active":"Actif","inactive":"Inactif","add":"Ajouter","save":"Enregistrer","terrain":"Service","kind":"Type","mandatory":"Obligatoire","basic":"De base","optional":"Optionnel","mandatory_year":"Année requise","any":"Selon le programme","period":"Période","places":"Nombre de places","used":"Utilisées","remaining":"Restantes","date":"Date de réalisation","academic_year":"Année universitaire","choose":"Choisir","assign_now":"Affecter un résident","check_save":"Vérifier et enregistrer","confirmed":"Confirmé","pending":"En attente","rejected":"Refusé","history_add":"Enregistrer un stage antérieur","reason":"Motif de décision","approve":"Approuver","reject":"Refuser","language":"Langue de l’interface","director":"Responsable","new_password":"Nouveau mot de passe (facultatif)","change":"Enregistrer les paramètres","note":"Changer de langue ne modifie pas les données.","priority":"Priorité aux 4e, puis 3e, 2e et 1re années.","none":"Aucune donnée","capacity_first":"Définissez d’abord la capacité du service et de la période","full":"Capacité complète","duplicate":"Résident déjà affecté pendant cette période au service : ","same_terrain_year":"Ce résident a déjà effectué ce service cette année, pendant la période : ","history_block":"Stage déjà effectué ; répétition bloquée avant d’avoir terminé tous les services.","history_repeat":"Répétition autorisée : tous les services ont été effectués.","mismatch":"Année différente de l’année requise ; décision du responsable nécessaire","done":"Enregistré","overview":"Vue annuelle des affectations","count":"Nombre d’affectations","type":"Catégorie" ,"export":"Exporter CSV","backup":"Télécharger la sauvegarde","all":"Tous les services","four":"Affectations confirmées / 4 périodes","waiting":"En attente","users":"Utilisateurs","import":"Importer","objectives":"Objectifs","exams":"Examens","dems":"Archive DEMS","audit":"Journal d’audit","restore":"Restaurer","username":"Identifiant","role":"Rôle","standard_user":"Utilisateur standard","super_admin":"Super Admin","created":"Créé le","active_col":"Actif","actor":"Acteur","action":"Action","details":"Détails","module":"Matière","theory":"Théorie","practical":"Pratique","success_date":"Date de réussite","file":"Fichier","objective":"Objectif","archive":"Archiver","users_help":"Créez un compte distinct pour chaque responsable et attribuez le rôle Super Admin à Pr Benhocine et Dr Dris.","import_help":"Importez une liste contenant le nom, le prénom et l’année d’étude. Vérifiez l’aperçu avant confirmation ; aucun stage passé ne sera inventé.","restore_help":"L’intégrité de la base sera vérifiée et une copie de la base actuelle sera créée avant la restauration.","confirm_password":"Confirmer le mot de passe","confirm_import":"Confirmer l’importation","cancel":"Annuler","upload_preview":"Charger et prévisualiser","archive_note":"Les données et l’historique du résident sont conservés, pas supprimés."},
"en":{"app":"ResiTrack","home":"Home","residents":"Residents","manage_residents":"Manage residents","import_residents":"Import residents","promotion":"Promotion decisions & exams","dems_success":"DEMS successful graduates","settings_page":"App settings","terrains":"Departments","capacities":"Capacity","assign":"Assignments","history":"History","summary":"Resident summary","decisions":"Decisions","settings":"Settings","logout":"Log out","login":"Administrator login","password":"Password","signin":"Sign in","badpass":"Incorrect password","year":"Academic year","resident":"Resident","surname":"Surname","firstname":"First name","study_year":"Year","phone":"Phone","repeat":"Repeating year","status":"Status","active":"Active","inactive":"Inactive","add":"Add","save":"Save","terrain":"Department","kind":"Type","mandatory":"Mandatory","basic":"Core","optional":"Optional","mandatory_year":"Required year","any":"As per curriculum","period":"Period","places":"Places","used":"Used","remaining":"Remaining","date":"Completion date","academic_year":"Academic year","choose":"Choose","assign_now":"Assign resident","check_save":"Validate and save","confirmed":"Confirmed","pending":"Pending decision","rejected":"Rejected","history_add":"Record previous rotation","reason":"Decision reason","approve":"Approve","reject":"Reject","language":"Interface language","director":"Administrator","new_password":"New password (optional)","change":"Save settings","note":"Changing language does not change saved data.","priority":"Priority: year 4, then 3, 2 and 1.","none":"No data","capacity_first":"Set capacity for this department and period first","full":"Capacity is full","duplicate":"Resident already assigned during this period to: ","same_terrain_year":"This resident already completed this department this academic year, during: ","history_block":"Rotation completed previously; repeats blocked until all departments are completed.","history_repeat":"Repeat allowed because all departments have been completed.","mismatch":"Year does not match required year; administrator decision needed","done":"Saved","overview":"Annual assignment overview","count":"Assignment count","type":"Category" ,"export":"Export CSV","backup":"Download backup","all":"All departments","four":"Confirmed assignments / 4 periods","waiting":"Pending","users":"Users","import":"Import","objectives":"Objectives","exams":"Exams","dems":"DEMS archive","audit":"Audit log","restore":"Restore","username":"Username","role":"Role","standard_user":"Standard user","super_admin":"Super Admin","created":"Created","active_col":"Active","actor":"Actor","action":"Action","details":"Details","module":"Module","theory":"Theory","practical":"Practical","success_date":"Success date","file":"File","objective":"Objective","archive":"Archive","users_help":"Create a separate account for each administrator and assign Super Admin to Pr Benhocine and Dr Dris.","import_help":"Upload a list containing surname, first name and study year. Review the preview before confirming; no past rotations are invented.","restore_help":"The database integrity will be checked and a copy of the current database will be created before restoring.","confirm_password":"Confirm password","confirm_import":"Confirm import","cancel":"Cancel","upload_preview":"Upload and preview","archive_note":"Resident data and history are retained, not deleted."}
}
def tr(k): return D.get(session.get("lang","ar"),D["ar"]).get(k,D["ar"].get(k,k))
def db():
 c=sqlite3.connect(DB,timeout=20); c.row_factory=sqlite3.Row; c.execute("PRAGMA foreign_keys=ON"); return c
def setting(c,k,default=""):
 r=c.execute("SELECT value FROM settings WHERE key=?",(k,)).fetchone(); return r["value"] if r else default
def hash_password(password):
 salt=os.urandom(16).hex()
 digest=hashlib.pbkdf2_hmac("sha256",password.encode("utf-8"),bytes.fromhex(salt),310000).hex()
 return "pbkdf2_sha256$"+salt+"$"+digest
def verify_password(password, stored):
 if stored.startswith("pbkdf2_sha256$"):
  try:
   _,salt,digest=stored.split("$",2)
   candidate=hashlib.pbkdf2_hmac("sha256",password.encode("utf-8"),bytes.fromhex(salt),310000).hex()
   return hmac.compare_digest(candidate,digest)
  except (ValueError,TypeError):
   return False
 return hmac.compare_digest(hashlib.sha256(password.encode("utf-8")).hexdigest(),stored)
def ensure_column(c, table, column, spec):
 existing={row[1] for row in c.execute("PRAGMA table_info("+table+")")}
 if column not in existing:
  c.execute("ALTER TABLE "+table+" ADD COLUMN "+column+" "+spec)
def audit_event(c, action, details):
 c.execute("INSERT INTO audit(action,details,actor) VALUES(?,?,?)",
           (action,str(details)[:1000],str(session.get("user","system"))))
def init():
 c=db()
 c.executescript("""
 CREATE TABLE IF NOT EXISTS residents(id INTEGER PRIMARY KEY,surname TEXT NOT NULL,firstname TEXT NOT NULL,year INTEGER NOT NULL CHECK(year BETWEEN 1 AND 4),phone TEXT DEFAULT '',repeat_year INTEGER DEFAULT 0,status TEXT DEFAULT 'active');
 CREATE TABLE IF NOT EXISTS terrains(id INTEGER PRIMARY KEY,name TEXT UNIQUE NOT NULL,kind TEXT DEFAULT 'basic',mandatory_year INTEGER DEFAULT 0,active INTEGER NOT NULL DEFAULT 1);
 CREATE TABLE IF NOT EXISTS periods(id INTEGER PRIMARY KEY,year_label TEXT NOT NULL,name TEXT NOT NULL,UNIQUE(year_label,name));
 CREATE TABLE IF NOT EXISTS capacities(id INTEGER PRIMARY KEY,year_label TEXT NOT NULL,terrain_id INTEGER,period_id INTEGER,places INTEGER NOT NULL,UNIQUE(year_label,terrain_id,period_id));
 CREATE TABLE IF NOT EXISTS assignments(id INTEGER PRIMARY KEY,resident_id INTEGER,terrain_id INTEGER,period_id INTEGER,status TEXT DEFAULT 'confirmed',UNIQUE(resident_id,period_id));
 CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY,resident_id INTEGER,terrain_id INTEGER,year_label TEXT,period TEXT,date_done TEXT);
 CREATE TABLE IF NOT EXISTS decisions(id INTEGER PRIMARY KEY,details TEXT,decision TEXT,reason TEXT,actor TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
 CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,action TEXT,details TEXT,actor TEXT DEFAULT '',created_at TEXT DEFAULT CURRENT_TIMESTAMP);
 CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
 """)
 # Additive migrations preserve existing resident and rotation-history records.
 for col, spec in {"birth_place":"TEXT DEFAULT ''","birth_date":"TEXT DEFAULT ''","photo_path":"TEXT DEFAULT ''","dems_status":"TEXT DEFAULT ''"}.items():
  ensure_column(c,"residents",col,spec)
 ensure_column(c,"terrains","active","INTEGER NOT NULL DEFAULT 1")
 ensure_column(c,"audit","actor","TEXT DEFAULT ''")
 c.executescript("""
 CREATE TABLE IF NOT EXISTS exam_records(id INTEGER PRIMARY KEY,resident_id INTEGER NOT NULL,study_year INTEGER NOT NULL,module TEXT NOT NULL,theory REAL NOT NULL,practical REAL NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
 CREATE TABLE IF NOT EXISTS objectives(id INTEGER PRIMARY KEY,terrain_id INTEGER NOT NULL,study_year INTEGER NOT NULL,objective TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS dems_archive(id INTEGER PRIMARY KEY,resident_id INTEGER NOT NULL UNIQUE,success_date TEXT NOT NULL,profile_json TEXT NOT NULL,history_json TEXT NOT NULL,archived_at TEXT DEFAULT CURRENT_TIMESTAMP);
 CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL CHECK(role IN ('super_admin','user')),active INTEGER NOT NULL DEFAULT 1,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
 CREATE TABLE IF NOT EXISTS import_previews(id INTEGER PRIMARY KEY,owner TEXT NOT NULL,rows_json TEXT NOT NULL,errors_json TEXT NOT NULL,filename TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
 """)
 y=str(datetime.now().year)+"-"+str(datetime.now().year+1)
 c.execute("INSERT OR IGNORE INTO settings VALUES('year',?)",(y,))
 initial_password=os.environ.get("ROTATION_INITIAL_PASSWORD")
 if initial_password and not setting(c,"password"):
  c.execute("INSERT OR IGNORE INTO settings VALUES('password',?)",(hash_password(initial_password),))
 c.execute("INSERT OR IGNORE INTO settings VALUES('director',?)",("Professor Benhocine",))
 for n,k in [("Réanimation chirurgicale","basic"),("Réanimation polyvalente","basic"),("Chirurgie générale","mandatory"),("Urologie","basic"),("Orthopédie","basic"),("Neurochirurgie","basic"),("Sédation","optional"),("Maxillo-faciale","optional"),("CCI","basic"),("Obstétrique","basic"),("Chirurgie cardiaque","optional"),("PU Médecine","basic"),("PU Chirurgie","basic"),("ORL","basic"),("Ophtalmologie","basic"),("Gynécologie","basic"),("Chirurgie thoracique","basic"),("Brûlés","optional"),("CAC DBK","optional")]:
  c.execute("INSERT OR IGNORE INTO terrains(name,kind) VALUES(?,?)",(n,k))
 y=setting(c,"year",y)
 if not c.execute("SELECT 1 FROM periods WHERE year_label=?",(y,)).fetchone():
  for n in ["01 Fév - 30 Avr","01 Mai - 30 Juillet","01 Août - 30 Oct","01 Nov - 30 Jan"]:
   c.execute("INSERT OR IGNORE INTO periods(year_label,name) VALUES(?,?)",(y,n))
 c.commit(); c.close()
@app.before_request
def boot():
 if not getattr(app,"_ready",False): init(); app._ready=True
def page(body,**kw):
 lang=session.get("lang","ar")
 shell="""<!doctype html><html lang="{{lang}}" dir="{{'rtl' if lang=='ar' else 'ltr'}}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#103c66"><meta name="application-name" content="ResiTrack"><link rel="icon" type="image/svg+xml" href="/static/resitrack-icon.svg"><title>{{t('app')}} — {{t('year')}}</title></head><style>*{box-sizing:border-box}html{width:100%;max-width:100%;overflow-x:hidden}body{font-family:Arial,sans-serif;background:#f1f5f9;margin:0;color:#182b3d;width:100%;max-width:100%;overflow-x:hidden;line-height:1.5}header{background:linear-gradient(135deg,#103c66 0%,#17689a 58%,#23a6a5 100%);color:white;padding:clamp(10px,3vw,18px);overflow-wrap:anywhere}.brand-lockup{display:flex;align-items:center;gap:14px;max-width:1050px;margin:0 auto}.brand-icon{width:clamp(48px,12vw,70px);height:auto;flex:0 0 auto;filter:drop-shadow(0 5px 5px #001b3380)}.brand-lockup h2{margin:0;font-size:clamp(21px,4vw,30px);letter-spacing:.2px}.brand-tagline{margin:2px 0 5px;opacity:.93;font-size:clamp(12px,2.5vw,15px)}.brand-year{font-size:12px;opacity:.9}main{width:100%;max-width:1050px;margin:0 auto;padding:clamp(7px,2.5vw,16px);min-width:0}nav{display:flex;align-items:flex-start;flex-wrap:wrap;gap:6px;overflow:visible;max-width:100%;background:white;padding:10px}.nav-group{position:relative;min-width:0}.nav-group summary{list-style:none;background:#164e83;color:white;padding:9px 12px;border-radius:7px;cursor:pointer;white-space:nowrap}.nav-group summary::-webkit-details-marker{display:none}.nav-group summary:after{content:" ▾";font-size:.85em}.nav-menu{display:flex;flex-direction:column;gap:5px;min-width:180px;padding:7px;margin-top:5px;background:#fff;border:1px solid #d7e1eb;border-radius:9px;box-shadow:0 6px 18px #182b3d22}.nav-menu a{display:block;width:100%}.main-nav>a{flex:0 0 auto}.nav-group[open]{z-index:10}.nav-group[open] .nav-menu{position:absolute;top:100%;inset-inline-start:0;max-width:min(85vw,280px);max-height:65vh;overflow:auto}.nav-group[open] .nav-menu a{white-space:normal}a,button{background:#164e83;color:white;padding:9px 12px;border:0;border-radius:7px;text-decoration:none;display:inline-block;white-space:normal;overflow-wrap:anywhere;max-width:100%;cursor:pointer}section{background:white;padding:clamp(9px,2.5vw,15px);border:1px solid #d7e1eb;border-radius:10px;margin:10px 0;min-width:0;max-width:100%;overflow-wrap:anywhere}input,select,textarea{font:inherit;padding:9px;border:1px solid #bccada;border-radius:7px;width:100%;max-width:100%;margin:4px 0 9px}label{display:block;min-width:0}table{border-collapse:collapse;width:100%;min-width:540px}td,th{text-align:start;border-bottom:1px solid #ddd;padding:8px;overflow-wrap:anywhere}.wrap{max-width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(170px,100%),1fr));gap:8px;min-width:0}.msg{background:#fff0c2;padding:10px;border-radius:7px;overflow-wrap:anywhere}.good{color:green}.bad{color:#b21d1d}.muted{color:#526274}img,video,iframe{max-width:100%;height:auto}@media(max-width:600px){main{padding:7px}header{font-size:clamp(13px,3.5vw,16px)}nav{padding:7px;gap:5px}.nav-group summary,nav>a{font-size:13px;padding:8px 9px}.nav-menu{min-width:min(220px,82vw)}section{margin:7px 0;padding:10px}.grid{grid-template-columns:minmax(0,1fr)}table{min-width:540px}} [dir=rtl]{text-align:right}[dir=rtl] nav{direction:rtl}
/* ResiTrack unified interior visual identity */
:root{--rt-navy:#142b49;--rt-blue:#2768a8;--rt-mint:#36cfae;--rt-cyan:#45c7e8;--rt-coral:#ff8b72;--rt-amber:#ffc36c;--rt-violet:#9b8cf5;--rt-ink:#21334b;--rt-line:#dce6f0;--rt-glass:#ffffffd9}
body{background:radial-gradient(ellipse at 8% 0%,#ffd2ad55,transparent 28%),radial-gradient(ellipse at 95% 22%,#7ce8d533,transparent 26%),linear-gradient(145deg,#f3f7fc,#edf3fa 58%,#f8f1f8);color:var(--rt-ink)}
header.brand-header{background:radial-gradient(ellipse at 85% 0%,#ffb66c45,transparent 34%),linear-gradient(115deg,#101d36,#1c4265 58%,#28566d);box-shadow:0 12px 32px #172d4825;border-bottom:3px solid transparent;border-image:linear-gradient(90deg,var(--rt-mint),var(--rt-cyan),var(--rt-coral),var(--rt-violet)) 1}
.brand-icon{filter:drop-shadow(0 7px 12px #0005)}main{padding-top:18px;padding-bottom:26px}
.main-nav{margin:0 auto;position:sticky;top:0;z-index:20;justify-content:center;align-items:center;gap:8px;background:#ffffffdf;backdrop-filter:blur(16px);border:1px solid #ffffff;border-bottom-color:#dce6f0;border-radius:0 0 18px 18px;box-shadow:0 9px 25px #17365b12}
.main-nav>a,.nav-group summary{border:1px solid #ffffff25;background:linear-gradient(135deg,#214e79,#286da2);box-shadow:0 4px 10px #1c42651a;transition:transform .18s ease,box-shadow .18s ease,filter .18s ease}
.main-nav>a:hover,.nav-group summary:hover{transform:translateY(-2px);box-shadow:0 7px 15px #1c42652a;filter:saturate(1.12)}
.main-nav>a:nth-of-type(1){background:linear-gradient(135deg,#2768a8,#3986c9)}
.main-nav>a:nth-of-type(2){background:linear-gradient(135deg,#168f88,#35c7a9)}
.main-nav>a:nth-of-type(3){background:linear-gradient(135deg,#cf7547,#ffab68)}
.main-nav>a:nth-of-type(4){background:linear-gradient(135deg,#6d62bf,#9c8df5)}
.nav-group summary{background:linear-gradient(135deg,#254a70,#477e9e)}
.nav-menu{background:#fffffff2;backdrop-filter:blur(15px);border:1px solid #d9e7f0;border-radius:14px;box-shadow:0 18px 45px #17365b25}
.nav-menu a{background:#f1f7fb;color:#244461;border:1px solid transparent;border-inline-start:3px solid var(--rt-cyan);border-radius:9px;transition:background .18s ease,transform .18s ease}
.nav-menu a:hover{background:#e3f7f1;transform:translateX(-2px)}
section{background:var(--rt-glass);backdrop-filter:blur(10px);border:1px solid #ffffff;box-shadow:0 9px 28px #2444610d;border-radius:17px;transition:box-shadow .2s ease}
section h2,section h3{color:#204c70}.nav-icon{display:inline-flex;align-items:center;justify-content:center;min-width:20px;margin-inline-end:5px;font-size:16px;line-height:1;color:#b9ffec}.nav-group summary .nav-icon{color:#ffcf91}.rt-quick-actions{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(210px,100%),1fr));gap:12px;margin:14px 0}.rt-action-card{display:flex;align-items:center;gap:13px;min-width:0;padding:15px;border-radius:16px;background:linear-gradient(135deg,#ffffffef,#f1f8fb);border:1px solid #fff;box-shadow:0 8px 22px #24446112;color:#244461;text-decoration:none}.rt-action-card:hover{transform:translateY(-3px)}.rt-action-icon{display:flex;align-items:center;justify-content:center;flex:0 0 46px;width:46px;height:46px;border-radius:14px;font-size:24px;color:#15364d;background:linear-gradient(135deg,#b9f6e8,#a8e8f7)}.rt-action-card:nth-child(2) .rt-action-icon{background:linear-gradient(135deg,#ffd6b2,#ffad8e)}.rt-action-card:nth-child(3) .rt-action-icon{background:linear-gradient(135deg,#d9d1ff,#b7b0fa)}.rt-action-card:nth-child(4) .rt-action-icon{background:linear-gradient(135deg,#fff0b9,#ffd18a)}.rt-action-card strong,.rt-action-card small{display:block}.rt-action-card strong{color:#214c6b}.rt-action-card small{font-size:12px;color:#657b8e}.rt-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(145px,100%),1fr));gap:10px;margin:14px 0}.rt-stat{padding:15px;border-radius:15px;background:linear-gradient(135deg,#fff,#f0f7fc);border:1px solid #fff;box-shadow:0 6px 18px #2444610d}.rt-stat span{display:block;font-size:12px;color:#617b8f}.rt-stat strong{display:block;font-size:26px;color:#214f73;line-height:1.3}.rt-stat:nth-child(2) strong{color:#15977f}.rt-stat:nth-child(3) strong{color:#c8754f}.rt-stat:nth-child(4) strong{color:#7668c5}.rt-dashboard-title{display:flex;align-items:center;gap:10px}.rt-dashboard-title .rt-dot{width:11px;height:11px;border-radius:50%;background:linear-gradient(135deg,var(--rt-mint),var(--rt-cyan));box-shadow:0 0 0 5px #42d9bd1b}.rt-year-chip{display:inline-flex;min-width:28px;justify-content:center;padding:3px 8px;border-radius:9px;background:#e4f0ff;color:#285a92;font-weight:700}.rt-progress{display:inline-block;vertical-align:middle;width:66px;height:7px;overflow:hidden;border-radius:10px;background:#e5edf4}.rt-progress span{display:block;height:100%;border-radius:10px;background:linear-gradient(90deg,#36cfae,#45c7e8)}.rt-resident-link{background:transparent;color:#275b7f;padding:2px 0;box-shadow:none}
section h2:after,section h3:after{content:"";display:block;width:54px;height:3px;margin-top:7px;border-radius:5px;background:linear-gradient(90deg,var(--rt-mint),var(--rt-cyan),var(--rt-coral))}
a,button{background:linear-gradient(135deg,#24659c,#2b80b1);box-shadow:0 3px 9px #214e7918;transition:filter .18s ease,transform .18s ease,box-shadow .18s ease}
a:hover,button:hover{filter:brightness(1.07) saturate(1.1);box-shadow:0 6px 14px #214e7925}
button:active,a:active{transform:translateY(1px)}
input,select,textarea{background:#ffffffdc;border-color:#c8d8e7;border-radius:11px;transition:border-color .15s ease,box-shadow .15s ease}
input:focus,select:focus,textarea:focus{outline:none;border-color:#37bfae;box-shadow:0 0 0 3px #37cfae26}
table{border-collapse:separate;border-spacing:0;border:1px solid var(--rt-line);border-radius:12px;overflow:hidden;background:#fff}
th{background:linear-gradient(100deg,#e7f4f7,#eef0fc);color:#234b68;font-weight:700}
td,th{border-bottom:1px solid #e7edf4;padding:10px}
tr:last-child td{border-bottom:0}
tbody tr:nth-child(even),table tr:nth-child(even){background:#f8fbfe}
.msg{background:linear-gradient(100deg,#fff2d8,#fff8eb);border:1px solid #f4d49a;color:#72501c;border-radius:12px}
.good{color:#13856d;font-weight:700}.bad{color:#c34e50;font-weight:700}.muted{color:#60758a}
.rt-language{display:flex;align-items:center;gap:5px;margin-inline-start:auto}
.rt-language a{padding:7px 9px;border-radius:20px;background:#e9f5f7;color:#244c66;border:1px solid #d5e8ef;box-shadow:none;font-size:12px}
.rt-language a[aria-current=page]{background:linear-gradient(100deg,#2ac7a7,#55c9e8);color:#102f47;font-weight:700}
.rt-footer{text-align:center;padding:17px 10px 10px;color:#637b91;font-size:12px}
.rt-footer strong{color:#2d5877}.rt-footer .rt-sep{color:#ff986c;padding:0 4px}
@media(max-width:600px){.main-nav{position:relative;border-radius:0 0 14px 14px;justify-content:flex-start}.rt-language{width:100%;justify-content:center;margin:3px 0 0}.main-nav>a,.nav-group summary{font-size:12px}.rt-footer{line-height:1.9}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{scroll-behavior:auto!important;transition:none!important;animation:none!important}}
</style><header class="brand-header"><div class="brand-lockup"><img class="brand-icon" src="/static/resitrack-icon.svg" width="64" height="64" alt="ResiTrack"><div><h2>{{t('app')}}</h2><p class="brand-tagline">{% if lang=='ar' %}تسيير تربصات الأطباء المقيمين{% elif lang=='fr' %}Gestion des stages des médecins résidents{% else %}Resident rotation management{% endif %}</p><span class="brand-year">{{t('year')}}: {{year}}</span></div></div></header>{% if user %}<nav class="main-nav"><a href="/"><span class="nav-icon">⌂</span>{{t('home')}}</a><details class="nav-group"><summary><span class="nav-icon">♙</span>{{t('residents')}}</summary><div class="nav-menu"><a href="/residents">{{t('manage_residents')}}</a><a href="/objectives">{{t('objectives')}}</a><a href="/import">{{t('import_residents')}}</a><a href="/exams">{{t('promotion')}}</a><a href="/dems">{{t('dems_success')}}</a></div></details><a href="/terrains"><span class="nav-icon">✚</span>{{t('terrains')}}</a><a href="/capacities"><span class="nav-icon">▦</span>{{t('capacities')}}</a><a href="/assign"><span class="nav-icon">⇄</span>{{t('assign')}}</a><a href="/history"><span class="nav-icon">◷</span>{{t('history')}}</a><a href="/decisions"><span class="nav-icon">✓</span>{{t('decisions')}}</a><a href="/summary"><span class="nav-icon">▤</span>{{t('summary')}}</a><details class="nav-group"><summary><span class="nav-icon">⚙</span>{{t('settings')}}</summary><div class="nav-menu"><a href="/settings">{{t('settings_page')}}</a><a href="/users">{{t('users')}}</a><a href="/audit">{{t('audit')}}</a><a href="/backup">{{t('backup')}}</a><a href="/export">{{t('export')}}</a><a href="/restore">{{t('restore')}}</a><a href="/logout">{{t('logout')}}</a></div></details><div class="rt-language" aria-label="Language"><a href="/lang/ar" {% if lang=='ar' %}aria-current="page"{% endif %} title="العربية">ع</a><a href="/lang/fr" {% if lang=='fr' %}aria-current="page"{% endif %} title="Français">FR</a><a href="/lang/en" {% if lang=='en' %}aria-current="page"{% endif %} title="English">EN</a></div></nav>{% endif %}<main>{% for m in get_flashed_messages() %}<p class="msg">{{m}}</p>{% endfor %}{{body|safe}}</main><footer class="rt-footer">© <strong>Tous droits réservés · Dr Dris</strong><span class="rt-sep"> | </span><strong>All rights reserved · Dr Dris</strong><span class="rt-sep"> | </span><strong>جميع الحقوق محفوظة · Dr Dris</strong></footer></html>"""
 context={"t":tr,"lang":lang,"year":setting(db(),"year")}
 context.update(kw)
 inner=render_template_string(body,**context)
 return render_template_string(shell,body=inner,lang=lang,t=tr,year=setting(db(),"year"),user=bool(session.get("user")),role=session.get("role",""))
def guard():
 if not session.get("user"): return redirect("/login")
def super_guard():
 if not session.get("user"): return redirect("/login")
 if session.get("role")!="super_admin": return ("Forbidden — Super Admin only",403)
@app.get("/lang/<lang>")
def lang(lang):
 if lang in LANGS: session["lang"]=lang
 return redirect(request.referrer or "/login")
@app.route("/login",methods=["GET","POST"])
def login():
 c=db(); p=setting(c,"password")
 if request.method=="POST":
  username=request.form.get("username","admin").strip()
  password=request.form.get("password","")
  account=c.execute("SELECT * FROM users WHERE username=? AND active=1",(username,)).fetchone()
  if not p:
   confirm=request.form.get("confirm_password","")
   if username!="admin" or len(password)<12 or password!=confirm:
    c.close(); flash("First setup requires username admin and matching password of at least 12 characters.")
    return redirect("/login")
   p=hash_password(password)
   c.execute("INSERT INTO settings(key,value) VALUES('password',?)",(p,))
   c.execute("INSERT OR IGNORE INTO users(username,password_hash,role) VALUES('admin',?,'super_admin')",(p,))
   c.commit(); c.close(); session.clear(); session["user"]="admin"; session["role"]="super_admin"; return redirect("/")
  if account and verify_password(password,account["password_hash"]):
   c.close(); session.clear(); session["user"]=account["username"]; session["role"]=account["role"]; return redirect("/")
  if username=="admin" and not account and verify_password(password,p):
   secure_hash=hash_password(password)
   c.execute("UPDATE settings SET value=? WHERE key='password'",(secure_hash,))
   c.execute("INSERT OR IGNORE INTO users(username,password_hash,role) VALUES('admin',?,'super_admin')",(secure_hash,))
   c.commit(); c.close(); session.clear(); session["user"]="admin"; session["role"]="super_admin"; return redirect("/")
  c.close(); flash(tr("badpass"))
 else:
  c.close()
 setup_required=not p
 return page("""<section class="login-hero"><div class="login-language"><span>🌐</span> <a href="/lang/ar">العربية</a><a href="/lang/fr">🇫🇷 Français</a><a href="/lang/en">🇬🇧 English</a></div><div class="login-brand"><div class="login-emblem" aria-hidden="true">💓</div><p class="login-kicker">CHU Nedir Mohamed · Tizi Ouzou</p><h1>Resi<span>Track</span></h1><p class="login-subtitle">Gestion des rotations des résidents</p><p class="login-motto">Aujourd’hui, un pas de plus vers votre avenir</p></div><div class="login-panel"><h2>{{t('login')}}</h2><p class="login-hint">Accédez à votre espace sécurisé</p><form method="post"><label>Username / Identifiant / اسم المستخدم</label><input name="username" value="admin" autocomplete="username" required><label>{{t('password')}}</label><div class="password-wrap"><input id="login-password" name="password" type="password" autocomplete="current-password" minlength="{{12 if setup_required else 1}}" required><button class="password-toggle" type="button" onclick="const p=document.getElementById('login-password');p.type=p.type==='password'?'text':'password';this.setAttribute('aria-label',p.type==='password'?'Show password':'Hide password')">◉</button></div>{% if setup_required %}<label>Confirm password / Confirmer le mot de passe / تأكيد كلمة المرور</label><input name="confirm_password" type="password" autocomplete="new-password" minlength="12" required><p>Create the first administrator password (12+ characters).</p>{% endif %}<button class="login-submit">{{'Create administrator / Créer l’administrateur / إنشاء المسؤول' if setup_required else t('signin')}} <span>➜</span></button></form><p class="login-security">♧ Connexion sécurisée · Secure sign-in · دخول آمن</p></div><div class="login-feature-row"><span>🩺 Médecine</span><span>💓 Réanimation</span><span>✨ Anesthésie</span><span>📋 Formation</span></div><footer class="login-rights">Tous droits réservés · Dr Dris <span>|</span> All rights reserved · Dr Dris <span>|</span> جميع الحقوق محفوظة · Dr Dris</footer></section><style>.login-hero{position:relative;isolation:isolate;overflow:hidden;max-width:980px;margin:12px auto;padding:clamp(16px,4vw,38px);border-radius:28px;color:#f8fbff;background:radial-gradient(ellipse at 12% 15%,#ffb36b55,transparent 32%),radial-gradient(ellipse at 88% 24%,#ef65b755,transparent 30%),radial-gradient(ellipse at 80% 85%,#39dfb355,transparent 30%),linear-gradient(135deg,#101d3a,#17365b 48%,#382b55);box-shadow:0 24px 60px #152d4c35}.login-hero:before,.login-hero:after{content:'';position:absolute;z-index:-1;border-radius:50%;filter:blur(2px);animation:orbit 12s ease-in-out infinite alternate}.login-hero:before{width:230px;height:230px;right:-55px;top:-75px;background:linear-gradient(135deg,#47e4d8aa,#4c8bff44)}.login-hero:after{width:190px;height:190px;left:-65px;bottom:90px;background:linear-gradient(135deg,#ff9a68aa,#d85bc955);animation-delay:-4s}.login-language{display:flex;justify-content:center;align-items:center;gap:clamp(8px,2vw,20px);flex-wrap:wrap}.login-language a{color:#fff;text-decoration:none;border:1px solid #ffffff45;background:#ffffff12;border-radius:22px;padding:7px 12px}.login-brand{text-align:center;padding:20px 0 14px}.login-emblem{font-size:56px;color:#53e2c4;text-shadow:0 0 28px #53e2c477;animation:pulse 3s ease-in-out infinite}.login-brand h1{font-size:clamp(38px,8vw,68px);line-height:1;margin:4px 0;font-weight:800;letter-spacing:-2px}.login-brand h1 span{background:linear-gradient(90deg,#43e5d1,#6db6ff,#ffb36b);-webkit-background-clip:text;background-clip:text;color:transparent}.login-kicker,.login-subtitle,.login-motto{margin:7px 0}.login-kicker{color:#b8d8f0}.login-subtitle{font-size:clamp(15px,3vw,20px)}.login-motto{color:#ffcf91;font-style:italic}.login-panel{max-width:480px;margin:16px auto 10px;padding:clamp(18px,4vw,30px);border:1px solid #ffffff55;border-radius:22px;background:#ffffff13;backdrop-filter:blur(14px);box-shadow:0 15px 35px #050d2040}.login-panel h2{text-align:center;margin:0;font-size:26px}.login-hint,.login-security{text-align:center;color:#d0e3f4}.login-panel label{display:block;margin-top:12px}.login-panel input{width:100%;min-width:0;background:#ffffff17;color:white;border:1px solid #ffffff48;border-radius:14px;padding:13px}.login-panel input::placeholder{color:#d4e2f1}.password-wrap{display:flex;align-items:center;gap:8px}.password-wrap input{flex:1}.password-toggle{border:1px solid #ffffff55;background:#ffffff18;color:white;padding:10px 14px;border-radius:12px;cursor:pointer}.login-submit{width:100%;margin-top:18px;border:0;border-radius:15px;padding:14px;background:linear-gradient(100deg,#5ce7b0,#22c9e5 55%,#6697ff);color:#08223d;font-weight:800;font-size:17px;box-shadow:0 7px 22px #31d5cf44;cursor:pointer}.login-submit span{margin-inline-start:10px}.login-feature-row{display:flex;justify-content:center;gap:10px;flex-wrap:wrap;margin:22px 0 12px}.login-feature-row span{border:1px solid #ffffff35;background:#ffffff10;border-radius:12px;padding:9px 13px}.login-rights{text-align:center;color:#d6e5f3;border-top:1px solid #ffffff24;padding-top:13px;font-size:12px}.login-rights span{color:#ffbe83;padding:0 5px}@keyframes orbit{to{transform:translate3d(-18px,22px,0) scale(1.08)}}@keyframes pulse{50%{transform:scale(1.08);filter:drop-shadow(0 0 12px #5ce7b0)}}@media(prefers-reduced-motion:reduce){.login-hero:before,.login-hero:after,.login-emblem{animation:none}}@media(max-width:520px){.login-hero{margin:4px;padding:14px;border-radius:18px}.login-feature-row span{font-size:12px;padding:7px}.login-rights span{padding:0 2px}}</style>""",setup_required=setup_required)
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
 return page("""<section><h3 class="rt-dashboard-title"><span class="rt-dot"></span>{{t('overview')}}</h3><p>{{t('priority')}}</p><div class="rt-stats"><div class="rt-stat"><span>{{t('residents')}}</span><strong>{{rows|length}}</strong></div><div class="rt-stat"><span>{{t('terrains')}}</span><strong>{{count}}</strong></div><div class="rt-stat"><span>{{t('confirmed')}}</span><strong>{{confirmed}}</strong></div><div class="rt-stat"><span>{{t('year')}}</span><strong style="font-size:17px">{{year}}</strong></div></div></section><div class="rt-quick-actions"><a class="rt-action-card" href="/residents"><span class="rt-action-icon">♙</span><span><strong>{{t('manage_residents')}}</strong><small>Profils · années · coordonnées</small></span></a><a class="rt-action-card" href="/assign"><span class="rt-action-icon">⇄</span><span><strong>{{t('assign')}}</strong><small>Répartition des stages</small></span></a><a class="rt-action-card" href="/terrains"><span class="rt-action-icon">✚</span><span><strong>{{t('terrains')}}</strong><small>Terrains obligatoires et optionnels</small></span></a><a class="rt-action-card" href="/import"><span class="rt-action-icon">⇧</span><span><strong>{{t('import_residents')}}</strong><small>Import avec aperçu et validation</small></span></a></div><section><h3 class="rt-dashboard-title"><span class="rt-dot"></span>{{t('four')}}</h3><div class="wrap"><table><tr><th>{{t('resident')}}</th><th>{{t('study_year')}}</th><th>{{t('count')}}</th></tr>{% for r,n in rows %}<tr><td><a class="rt-resident-link" href="/profile/{{r.id}}">{{r.surname}} {{r.firstname}}</a></td><td><span class="rt-year-chip">{{r.year}}</span></td><td><span class="rt-progress"><span style="width:{{[n*25,100]|min}}%"></span></span> {{n}} / 4</td></tr>{% else %}<tr><td colspan="3">{{t('none')}}</td></tr>{% endfor %}</table></div></section>""",rows=rows,count=count,confirmed=confirmed,year=y)
@app.route("/residents",methods=["GET","POST"])
def residents():
 if guard(): return redirect("/login")
 c=db()
 if request.method=="POST":
  if request.form.get("action")=="edit":
   if session.get("role")!="super_admin": c.close(); return ("Forbidden — Super Admin only",403)
   rid=int(request.form["rid"])
   c.execute("UPDATE residents SET year=?,repeat_year=?,status=? WHERE id=?",(int(request.form["year"]),int(request.form.get("repeat_year","0")),request.form["status"],rid))
   audit_event(c,"resident.updated",f"resident_id={rid}; year={request.form['year']}; status={request.form['status']}")
  else:
   c.execute("INSERT INTO residents(surname,firstname,year,phone,repeat_year,status) VALUES(?,?,?,?,?,?)",(request.form["surname"].strip(),request.form["firstname"].strip(),int(request.form["year"]),request.form.get("phone",""),int(request.form.get("repeat_year","0")),"active"))
   audit_event(c,"resident.created",request.form["surname"].strip()+" "+request.form["firstname"].strip())
  c.commit(); flash(tr("done"))
 rows=c.execute("SELECT * FROM residents ORDER BY status DESC,year DESC,surname").fetchall(); c.close()
 return page("""<section><h3>{{t('add')}} — {{t('resident')}}</h3><form method="post"><div class="grid"><div><label>{{t('surname')}}</label><input name="surname" required></div><div><label>{{t('firstname')}}</label><input name="firstname" required></div><div><label>{{t('study_year')}}</label><select name="year">{% for y in range(1,5) %}<option>{{y}}</option>{% endfor %}</select></div><div><label>{{t('phone')}}</label><input name="phone"></div></div><label><input type="checkbox" name="repeat_year" value="1"> {{t('repeat')}}</label><button>{{t('add')}}</button></form></section><section><div class="wrap"><table><tr><th>{{t('resident')}}</th><th>{{t('study_year')}}</th><th>{{t('save')}}</th></tr>{% for r in rows %}<tr><td><a href="/profile/{{r.id}}">{{r.surname}} {{r.firstname}}</a></td><td>{{r.year}}</td><td><form method="post"><input type="hidden" name="action" value="edit"><input type="hidden" name="rid" value="{{r.id}}"><select name="year">{% for y in range(1,5) %}<option value="{{y}}" {% if r.year==y %}selected{% endif %}>{{y}}</option>{% endfor %}</select><label><input type="checkbox" name="repeat_year" value="1" {% if r.repeat_year %}checked{% endif %}> {{t('repeat')}}</label><select name="status"><option value="active" {% if r.status=='active' %}selected{% endif %}>{{t('active')}}</option><option value="inactive" {% if r.status=='inactive' %}selected{% endif %}>{{t('inactive')}}</option><option value="graduated" {% if r.status=='graduated' %}selected{% endif %}>Graduated / Diplômé / متخرج</option></select><button>{{t('save')}}</button></form></td></tr>{% endfor %}</table></div></section>""",rows=rows)
@app.route("/terrains",methods=["GET","POST"])
def terrains():
 if guard(): return redirect("/login")
 c=db()
 if request.method=="POST":
  if session.get("role")!="super_admin": c.close(); return ("Forbidden — Super Admin only",403)
  action=request.form.get("action","create")
  try:
   if action=="edit":
    tid=int(request.form["tid"]); name=request.form["name"].strip(); kind=request.form["kind"]; mandatory_year=int(request.form["mandatory_year"])
    if not name or kind not in ("mandatory","basic","optional") or mandatory_year not in (0,1,2,3,4): raise ValueError("Invalid terrain fields")
    c.execute("UPDATE terrains SET name=?,kind=?,mandatory_year=? WHERE id=?",(name,kind,mandatory_year,tid))
    audit_event(c,"terrain.updated",f"terrain_id={tid}; name={name}; kind={kind}; mandatory_year={mandatory_year}")
   elif action in ("deactivate","activate"):
    tid=int(request.form["tid"]); active=0 if action=="deactivate" else 1
    c.execute("UPDATE terrains SET active=? WHERE id=?",(active,tid))
    audit_event(c,"terrain.deactivated" if not active else "terrain.activated",f"terrain_id={tid}")
   else:
    name=request.form["name"].strip(); kind=request.form["kind"]; mandatory_year=int(request.form["mandatory_year"])
    if not name or kind not in ("mandatory","basic","optional") or mandatory_year not in (0,1,2,3,4): raise ValueError("Invalid terrain fields")
    c.execute("INSERT INTO terrains(name,kind,mandatory_year) VALUES(?,?,?)",(name,kind,mandatory_year))
    audit_event(c,"terrain.created",name+" kind="+kind)
   c.commit(); flash(tr("done"))
  except sqlite3.IntegrityError: c.rollback(); flash("Already exists / Existe déjà / المصلحة موجودة")
  except ValueError as exc: c.rollback(); flash(str(exc))
 rows=c.execute("SELECT * FROM terrains ORDER BY CASE WHEN kind='optional' THEN 1 ELSE 0 END, name").fetchall(); c.close()
 return page("""<section><h3>{{t('add')}} — {{t('terrain')}}</h3><form method="post"><input type="hidden" name="action" value="create"><label>{{t('terrain')}}</label><input name="name" required><div class="grid"><div><label>{{t('kind')}}</label><select name="kind"><option value="mandatory">{{t('mandatory')}}</option><option value="basic">{{t('basic')}}</option><option value="optional">{{t('optional')}}</option></select></div><div><label>{{t('mandatory_year')}}</label><select name="mandatory_year"><option value="0">{{t('any')}}</option>{% for y in range(1,5) %}<option value="{{y}}">{{y}}</option>{% endfor %}</select></div></div><button>{{t('save')}}</button></form></section><section><div class="wrap"><table><tr><th>{{t('terrain')}}</th><th>{{t('kind')}}</th><th>{{t('mandatory_year')}}</th><th>{{t('status')}}</th><th>Admin actions</th></tr>{% for r in rows %}<tr><td colspan="5"><form method="post" class="grid"><input type="hidden" name="action" value="edit"><input type="hidden" name="tid" value="{{r.id}}"><input name="name" value="{{r.name}}" required><select name="kind"><option value="mandatory" {% if r.kind=='mandatory' %}selected{% endif %}>{{t('mandatory')}}</option><option value="basic" {% if r.kind=='basic' %}selected{% endif %}>{{t('basic')}}</option><option value="optional" {% if r.kind=='optional' %}selected{% endif %}>{{t('optional')}}</option></select><select name="mandatory_year"><option value="0" {% if not r.mandatory_year %}selected{% endif %}>{{t('any')}}</option>{% for y in range(1,5) %}<option value="{{y}}" {% if r.mandatory_year==y %}selected{% endif %}>{{y}}</option>{% endfor %}</select><span>{{'Active' if r.active else 'Inactive'}}</span><button>{{t('save')}}</button></form>{% if role=='super_admin' %}<form method="post"><input type="hidden" name="tid" value="{{r.id}}"><button name="action" value="{{'deactivate' if r.active else 'activate'}}">{{'Deactivate' if r.active else 'Reactivate'}}</button></form>{% endif %}</td></tr>{% endfor %}</table></div><p>Deactivation hides a terrain from new assignments but preserves all past history.</p></section>""",rows=rows)
@app.route("/capacities",methods=["GET","POST"])
def capacities():
 if guard(): return redirect("/login")
 c=db(); y=setting(c,"year")
 if request.method=="POST":
  if session.get("role")!="super_admin": c.close(); return ("Forbidden — Super Admin only",403)
  tid,pid,places=int(request.form["terrain"]),int(request.form["period"]),max(0,int(request.form["places"]))
  used=c.execute("SELECT COUNT(*) FROM assignments WHERE terrain_id=? AND period_id=? AND status IN ('confirmed','pending')",(tid,pid)).fetchone()[0]
  if places<used: flash(tr("full"))
  else:
   c.execute("INSERT INTO capacities(year_label,terrain_id,period_id,places) VALUES(?,?,?,?) ON CONFLICT(year_label,terrain_id,period_id) DO UPDATE SET places=excluded.places",(y,tid,pid,places))
   audit_event(c,"capacity.changed",f"year={y}; terrain_id={tid}; period_id={pid}; places={places}")
   c.commit(); flash(tr("done"))
 ts=c.execute("SELECT * FROM terrains WHERE active=1 ORDER BY CASE WHEN kind='optional' THEN 1 ELSE 0 END, name").fetchall(); ps=c.execute("SELECT * FROM periods WHERE year_label=? ORDER BY id",(y,)).fetchall()
 rows=c.execute("SELECT t.name terrain,p.name period,cap.places,(SELECT COUNT(*) FROM assignments a WHERE a.terrain_id=t.id AND a.period_id=p.id AND a.status IN ('confirmed','pending')) used FROM capacities cap JOIN terrains t ON t.id=cap.terrain_id JOIN periods p ON p.id=cap.period_id WHERE cap.year_label=?",(y,)).fetchall(); c.close()
 return page("""<section><h3>{{t('capacities')}}</h3><form method="post"><div class="grid"><div><label>{{t('terrain')}}</label><select name="terrain">{% for x in ts %}<option value="{{x.id}}">{{x.name}}</option>{% endfor %}</select></div><div><label>{{t('period')}}</label><select name="period">{% for x in ps %}<option value="{{x.id}}">{{x.name}}</option>{% endfor %}</select></div><div><label>{{t('places')}}</label><input type="number" min="0" name="places" required></div></div><button>{{t('save')}}</button></form></section><section><div class="wrap"><table><tr><th>{{t('period')}}</th><th>{{t('terrain')}}</th><th>{{t('places')}}</th><th>{{t('used')}}</th><th>{{t('remaining')}}</th></tr>{% for r in rows %}<tr><td>{{r.period}}</td><td>{{r.terrain}}</td><td>{{r.places}}</td><td>{{r.used}}</td><td>{{r.places-r.used}}</td></tr>{% endfor %}</table></div></section>""",ts=ts,ps=ps,rows=rows)
def check(c,rid,tid,pid,y):
 r=c.execute("SELECT * FROM residents WHERE id=? AND status='active'",(rid,)).fetchone(); t=c.execute("SELECT * FROM terrains WHERE id=?",(tid,)).fetchone(); p=c.execute("SELECT * FROM periods WHERE id=? AND year_label=?",(pid,y)).fetchone()
 if not r or not t or not t["active"] or not p: return False,tr("none"),None
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
     audit_event(c,"assignment.replaced",f"assignment_id={old['id']}; resident_id={rid}; terrain_id={tid}; status={status}")
     c.commit(); flash(msg)
    else:
     c.execute("INSERT INTO assignments(resident_id,terrain_id,period_id,status) VALUES(?,?,?,?)",(rid,tid,pid,status))
     audit_event(c,"assignment.created",f"resident_id={rid}; terrain_id={tid}; period_id={pid}; status={status}")
     c.commit(); flash(msg)
  except Exception: c.rollback(); flash("Invalid assignment / Affectation invalide / تعيين غير صالح")
 rs=c.execute("SELECT * FROM residents WHERE status='active' ORDER BY year DESC,surname").fetchall(); ts=c.execute("SELECT * FROM terrains WHERE active=1 ORDER BY CASE WHEN kind='optional' THEN 1 ELSE 0 END, name").fetchall(); ps=c.execute("SELECT * FROM periods WHERE year_label=? ORDER BY id",(y,)).fetchall()
 rows=c.execute("SELECT a.*,r.surname,r.firstname,r.year,t.name terrain,p.name period FROM assignments a JOIN residents r ON r.id=a.resident_id JOIN terrains t ON t.id=a.terrain_id JOIN periods p ON p.id=a.period_id WHERE p.year_label=? ORDER BY p.id,r.year DESC",(y,)).fetchall(); c.close()
 return page("""<section><h3>{{t('assign_now')}}</h3><p>{{t('priority')}}</p><form method="post"><label>{{t('resident')}}</label><select name="resident">{% for r in rs %}<option value="{{r.id}}">{{r.year}} — {{r.surname}} {{r.firstname}}</option>{% endfor %}</select><label>{{t('terrain')}}</label><select name="terrain">{% for x in ts %}<option value="{{x.id}}">{{x.name}}</option>{% endfor %}</select><label>{{t('period')}}</label><select name="period">{% for x in ps %}<option value="{{x.id}}">{{x.name}}</option>{% endfor %}</select><button>{{t('check_save')}}</button></form></section><section><div class="wrap"><table><tr><th>{{t('period')}}</th><th>{{t('resident')}}</th><th>{{t('study_year')}}</th><th>{{t('terrain')}}</th><th>{{t('status')}}</th><th>Admin action</th></tr>{% for a in rows %}<tr><td>{{a.period}}</td><td>{{a.surname}} {{a.firstname}}</td><td>{{a.year}}</td><td>{{a.terrain}}</td><td>{{t(a.status) if a.status in ['confirmed','pending','rejected'] else a.status}}</td><td>{% if role=='super_admin' and a.status not in ['cancelled','rejected'] %}<form method="post" action="/assignments/{{a.id}}/cancel"><button>Cancel</button></form>{% endif %}</td></tr>{% endfor %}</table></div></section>""",rs=rs,ts=ts,ps=ps,rows=rows)
@app.post("/assignments/<int:aid>/cancel")
def cancel_assignment(aid):
 if super_guard(): return super_guard()
 c=db()
 row=c.execute("SELECT status FROM assignments WHERE id=?",(aid,)).fetchone()
 if not row:
  c.close(); return ("Assignment not found",404)
 if row["status"]=="cancelled":
  c.close(); flash("Assignment already cancelled."); return redirect("/assign")
 c.execute("UPDATE assignments SET status='cancelled' WHERE id=?",(aid,))
 audit_event(c,"assignment.cancelled",f"assignment_id={aid}; previous_status={row['status']}")
 c.commit(); c.close(); flash("Assignment cancelled; historical record retained.")
 return redirect("/assign")
@app.route("/history",methods=["GET","POST"])
def history():
 if guard():return redirect("/login")
 c=db()
 if request.method=="POST":
  if session.get("role")!="super_admin": c.close(); return ("Forbidden — Super Admin only",403)
  rid=int(request.form["resident"]); tid=int(request.form["terrain"])
  c.execute("INSERT INTO history(resident_id,terrain_id,year_label,period,date_done) VALUES(?,?,?,?,?)",(rid,tid,request.form["year_label"],request.form.get("period",""),request.form.get("date_done","")))
  audit_event(c,"history.created",f"resident_id={rid}; terrain_id={tid}; year={request.form['year_label']}")
  c.commit(); flash(tr("done"))
 rs=c.execute("SELECT * FROM residents ORDER BY year DESC,surname").fetchall(); ts=c.execute("SELECT * FROM terrains WHERE active=1 ORDER BY CASE WHEN kind='optional' THEN 1 ELSE 0 END, name").fetchall(); rows=c.execute("SELECT h.*,r.surname,r.firstname,t.name terrain FROM history h JOIN residents r ON r.id=h.resident_id JOIN terrains t ON t.id=h.terrain_id ORDER BY h.id DESC").fetchall(); c.close()
 return page("""<section><h3>{{t('history_add')}}</h3><form method="post"><label>{{t('resident')}}</label><select name="resident">{% for r in rs %}<option value="{{r.id}}">{{r.surname}} {{r.firstname}} — {{r.year}}</option>{% endfor %}</select><label>{{t('terrain')}}</label><select name="terrain">{% for x in ts %}<option value="{{x.id}}">{{x.name}}</option>{% endfor %}</select><label>{{t('academic_year')}}</label><input name="year_label" required placeholder="2025-2026"><label>{{t('period')}}</label><input name="period"><label>{{t('date')}}</label><input type="date" name="date_done"><button>{{t('save')}}</button></form></section><section><div class="wrap"><table><tr><th>{{t('resident')}}</th><th>{{t('terrain')}}</th><th>{{t('academic_year')}}</th><th>{{t('period')}}</th><th>{{t('date')}}</th></tr>{% for h in rows %}<tr><td>{{h.surname}} {{h.firstname}}</td><td>{{h.terrain}}</td><td>{{h.year_label}}</td><td>{{h.period}}</td><td>{{h.date_done}}</td></tr>{% endfor %}</table></div></section>""",rs=rs,ts=ts,rows=rows)
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
 if super_guard():return super_guard()
 c=db()
 if request.method=="POST":
  aid=int(request.form["aid"]); outcome=request.form["outcome"]; reason=request.form.get("reason","").strip()
  if outcome not in ("approve","reject"): c.close(); return ("Invalid decision",400)
  a=c.execute("SELECT a.*,r.surname,r.firstname,t.name terrain,p.name period,p.year_label FROM assignments a JOIN residents r ON r.id=a.resident_id JOIN terrains t ON t.id=a.terrain_id JOIN periods p ON p.id=a.period_id WHERE a.id=? AND a.status='pending'",(aid,)).fetchone()
  if a and reason:
   if outcome=="approve":
    cap=c.execute("SELECT places FROM capacities WHERE year_label=? AND terrain_id=? AND period_id=?",(a["year_label"],a["terrain_id"],a["period_id"])).fetchone()
    used=c.execute("SELECT COUNT(*) FROM assignments WHERE terrain_id=? AND period_id=? AND status='confirmed'",(a["terrain_id"],a["period_id"])).fetchone()[0]
    dup=c.execute("SELECT id FROM assignments WHERE resident_id=? AND period_id=? AND id<>? AND status IN ('confirmed','pending')",(a["resident_id"],a["period_id"],aid)).fetchone()
    if not cap or used>=cap["places"] or dup: flash(tr("full") if not dup else tr("duplicate"))
    else:
     c.execute("UPDATE assignments SET status='confirmed' WHERE id=?",(aid,)); c.execute("INSERT INTO decisions(details,decision,reason,actor) VALUES(?,?,?,?)",(a["surname"]+" "+a["firstname"]+" — "+a["terrain"],tr("approve"),reason,session["user"]))
     audit_event(c,"assignment.override_approved",f"assignment_id={aid}; reason={reason}")
     c.commit(); flash(tr("done"))
   else:
    c.execute("UPDATE assignments SET status='rejected' WHERE id=?",(aid,)); c.execute("INSERT INTO decisions(details,decision,reason,actor) VALUES(?,?,?,?)",(a["surname"]+" "+a["firstname"]+" — "+a["terrain"],tr("reject"),reason,session["user"]))
    audit_event(c,"assignment.override_rejected",f"assignment_id={aid}; reason={reason}")
    c.commit(); flash(tr("done"))
 pending=c.execute("SELECT a.id,r.surname,r.firstname,r.year,t.name terrain,p.name period FROM assignments a JOIN residents r ON r.id=a.resident_id JOIN terrains t ON t.id=a.terrain_id JOIN periods p ON p.id=a.period_id WHERE a.status='pending'").fetchall(); ds=c.execute("SELECT * FROM decisions ORDER BY id DESC").fetchall(); c.close()
 return page("""<section><h3>{{t('decisions')}}</h3>{% for a in pending %}<p><b>{{a.surname}} {{a.firstname}}</b> — {{a.terrain}} / {{a.period}}</p><form method="post"><input type="hidden" name="aid" value="{{a.id}}"><input name="reason" placeholder="{{t('reason')}}" required><button name="outcome" value="approve">{{t('approve')}}</button> <button name="outcome" value="reject">{{t('reject')}}</button></form>{% else %}<p>{{t('none')}}</p>{% endfor %}</section><section><div class="wrap"><table><tr><th>Date</th><th>{{t('assign')}}</th><th>{{t('status')}}</th><th>{{t('reason')}}</th></tr>{% for d in ds %}<tr><td>{{d.created_at}}</td><td>{{d.details}}</td><td>{{d.decision}}</td><td>{{d.reason}}</td></tr>{% endfor %}</table></div></section>""",pending=pending,ds=ds)
@app.route("/settings",methods=["GET","POST"])
def settings():
 if super_guard():return super_guard()
 c=db()
 if request.method=="POST":
  lang=request.form.get("lang","ar")
  if lang in LANGS:session["lang"]=lang
  y=request.form.get("year","").strip()
  if y and (not re.fullmatch(r"\d{4}-\d{4}",y) or int(y.split("-")[1])!=int(y.split("-")[0])+1):
   flash("Academic year must be formatted as YYYY-YYYY with consecutive years.")
   y=setting(c,"year")
  if y:
   c.execute("INSERT INTO settings(key,value) VALUES('year',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(y,))
   if not c.execute("SELECT 1 FROM periods WHERE year_label=?",(y,)).fetchone():
    for n in ["01 Fév - 30 Avr","01 Mai - 30 Juillet","01 Août - 30 Oct","01 Nov - 30 Jan"]:c.execute("INSERT OR IGNORE INTO periods(year_label,name) VALUES(?,?)",(y,n))
  d=request.form.get("director","").strip()
  if d:c.execute("INSERT INTO settings(key,value) VALUES('director',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(d,))
  pw=request.form.get("new_password","")
  if pw:
   secure_hash=hash_password(pw)
   c.execute("INSERT INTO settings(key,value) VALUES('password',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(secure_hash,))
   c.execute("UPDATE users SET password_hash=? WHERE username=?",(secure_hash,session.get("user","admin")))
   audit_event(c,"security.password_changed","Administrator password changed")
  audit_event(c,"settings.updated",f"year={y}; director_updated={bool(d)}")
  c.commit(); flash(tr("done"))
 vals={r["key"]:r["value"] for r in c.execute("SELECT key,value FROM settings")}; c.close()
 return page("""<section><h3>{{t('settings')}}</h3><form method="post"><label>{{t('language')}}</label><select name="lang"><option value="ar" {% if lang=='ar' %}selected{% endif %}>العربية</option><option value="fr" {% if lang=='fr' %}selected{% endif %}>Français</option><option value="en" {% if lang=='en' %}selected{% endif %}>English</option></select><label>{{t('year')}}</label><input name="year" value="{{vals.get('year','')}}" required><label>{{t('director')}}</label><input name="director" value="{{vals.get('director','')}}"><label>{{t('new_password')}}</label><input type="password" name="new_password"><button>{{t('change')}}</button></form><p class="muted">{{t('note')}}</p></section>""",vals=vals,lang=session.get("lang","ar"))
@app.route("/users",methods=["GET","POST"])
def manage_users():
 if super_guard(): return super_guard()
 c=db()
 if request.method=="POST":
  action=request.form.get("action","create")
  if action in ("deactivate","activate"):
   uid=int(request.form["user_id"])
   target=c.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
   if not target: flash("User not found.")
   elif action=="deactivate" and target["username"]==session.get("user"): flash("You cannot deactivate your own account while signed in.")
   elif action=="deactivate" and target["role"]=="super_admin" and target["active"] and c.execute("SELECT COUNT(*) FROM users WHERE role='super_admin' AND active=1").fetchone()[0]<=1: flash("At least one active Super Admin must remain.")
   else:
    active=0 if action=="deactivate" else 1
    c.execute("UPDATE users SET active=? WHERE id=?",(active,uid))
    audit_event(c,"user.deactivated" if not active else "user.activated",f"username={target['username']}")
    c.commit(); flash(tr("done"))
  else:
   username=request.form.get("username","").strip()
   password=request.form.get("password","")
   role=request.form.get("role","user")
   if len(username)<3 or len(password)<12 or role not in ("super_admin","user"):
    flash("Username must have 3+ characters and password 12+ characters.")
   else:
    try:
     c.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",(username,hash_password(password),role))
     audit_event(c,"user.created",f"username={username}; role={role}")
     c.commit(); flash(tr("done"))
    except sqlite3.IntegrityError:
     flash("Username already exists.")
 rows=c.execute("SELECT id,username,role,active,created_at FROM users ORDER BY role DESC,username").fetchall(); c.close()
 return page("""<section><h3>{{t('users')}}</h3><p>{{t('users_help')}}</p><form method="post"><input type="hidden" name="action" value="create"><label>{{t('username')}}</label><input name="username" minlength="3" required><label>{{t('password')}} (12+)</label><input name="password" type="password" minlength="12" required><label>{{t('role')}}</label><select name="role"><option value="user">{{t('standard_user')}}</option><option value="super_admin">{{t('super_admin')}}</option></select><button>{{t('add')}}</button></form></section><section><div class="wrap"><table><tr><th>{{t('username')}}</th><th>{{t('role')}}</th><th>{{t('active_col')}}</th><th>{{t('created')}}</th><th>Admin action</th></tr>{% for u in rows %}<tr><td>{{u.username}}</td><td>{{u.role}}</td><td>{{u.active}}</td><td>{{u.created_at}}</td><td>{% if u.username!=session.get('user') or u.active==0 %}<form method="post"><input type="hidden" name="user_id" value="{{u.id}}"><button name="action" value="{{'deactivate' if u.active else 'activate'}}">{{'Deactivate' if u.active else 'Activate'}}</button></form>{% else %}Current account{% endif %}</td></tr>{% endfor %}</table></div></section>""",rows=rows)
@app.get("/audit")
def audit_log():
 if super_guard(): return super_guard()
 c=db(); rows=c.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 300").fetchall(); c.close()
 return page("""<section><h3>{{t('audit')}}</h3><div class="wrap"><table><tr><th>{{t('date')}}</th><th>{{t('actor')}}</th><th>{{t('action')}}</th><th>{{t('details')}}</th></tr>{% for r in rows %}<tr><td>{{r.created_at}}</td><td>{{r.actor}}</td><td>{{r.action}}</td><td>{{r.details}}</td></tr>{% else %}<tr><td colspan="4">{{t('none')}}</td></tr>{% endfor %}</table></div></section>""",rows=rows)
def normalize_header(value):
 value=str(value or "").strip().lower()
 value=re.sub(r"[\s_\-]+"," ",value)
 aliases={
  "surname":"surname","nom":"surname","family name":"surname","last name":"surname","اللقب":"surname",
  "firstname":"firstname","first name":"firstname","prénom":"firstname","prenom":"firstname","given name":"firstname","الاسم":"firstname",
  "year":"year","study year":"year","année":"year","annee":"year","niveau":"year","السنة":"year",
  "phone":"phone","telephone":"phone","téléphone":"phone","mobile":"phone","الهاتف":"phone",
  "birth place":"birth_place","lieu de naissance":"birth_place","مكان الميلاد":"birth_place",
  "birth date":"birth_date","date de naissance":"birth_date","تاريخ الميلاد":"birth_date"
 }
 return aliases.get(value,value.replace(" ","_"))
def parse_import_file(path, extension):
 rows=[]
 if extension==".csv":
  with open(path,"r",encoding="utf-8-sig",newline="") as handle:
   sample=handle.read(4096); handle.seek(0)
   try: dialect=csv.Sniffer().sniff(sample,delimiters=",;\t")
   except csv.Error: dialect=csv.excel
   rows=list(csv.reader(handle,dialect))
 elif extension in (".xlsx",".xls"):
  if extension==".xlsx":
   from openpyxl import load_workbook
   book=load_workbook(path,read_only=True,data_only=True)
   rows=[list(row) for row in book.active.iter_rows(values_only=True)]
   book.close()
  else:
   import xlrd
   book=xlrd.open_workbook(path)
   sheet=book.sheet_by_index(0)
   rows=[[sheet.cell_value(r,c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
 elif extension==".docx":
  from docx import Document
  doc=Document(path)
  if doc.tables:
   table=doc.tables[0]
   rows=[[cell.text.strip() for cell in row.cells] for row in table.rows]
  else:
   rows=[re.split(r"[,;\t]+",p.text.strip()) for p in doc.paragraphs if p.text.strip()]
 elif extension==".pdf":
  from pypdf import PdfReader
  text_content="\n".join(page.extract_text() or "" for page in PdfReader(path).pages)
  if not text_content.strip(): raise ValueError("The PDF has no extractable text (it may be scanned). Please provide a text-based PDF or spreadsheet.")
  lines=[line.strip() for line in text_content.splitlines() if line.strip()]
  delimiter=";" if sum(x.count(";") for x in lines)>sum(x.count(",") for x in lines) else ("\t" if any("\t" in x for x in lines) else ",")
  rows=[next(csv.reader([line],delimiter=delimiter)) for line in lines]
 elif extension==".doc":
  try:
   result=subprocess.run(["antiword",path],capture_output=True,text=True,check=True,timeout=20)
   document_text=result.stdout
  except FileNotFoundError:
   try:
    with tempfile.TemporaryDirectory(prefix="rotation_doc_") as converted_dir:
     subprocess.run(["libreoffice","--headless","--convert-to","txt:Text","--outdir",converted_dir,path],capture_output=True,text=True,check=True,timeout=30)
     converted_path=os.path.join(converted_dir,os.path.splitext(os.path.basename(path))[0]+".txt")
     with open(converted_path,"r",encoding="utf-8",errors="replace") as handle: document_text=handle.read()
   except (FileNotFoundError,subprocess.CalledProcessError,subprocess.TimeoutExpired) as exc:
    raise ValueError("Legacy .doc requires antiword or LibreOffice; convert it to .docx if neither is installed.") from exc
  lines=[line.strip() for line in document_text.splitlines() if line.strip()]
  rows=[re.split(r"\s*[,;\t]\s*",line) for line in lines]
 if not rows: raise ValueError("No table rows could be read from this file.")
 header=[normalize_header(x) for x in rows[0]]
 required={"surname","firstname","year"}
 if not required.issubset(set(header)):
  raise ValueError("Missing required columns. Include surname/nom/اللقب, firstname/prénom/الاسم, and year/année/السنة in the first row.")
 parsed=[]
 for line_number,values in enumerate(rows[1:],start=2):
  if not any(str(x or "").strip() for x in values): continue
  item={}
  for i,key in enumerate(header):
   if key and i<len(values): item[key]=str(values[i] if values[i] is not None else "").strip()
  item["row_number"]=line_number
  parsed.append(item)
 if not parsed: raise ValueError("The file contains headers but no resident rows.")
 return parsed
@app.route("/import",methods=["GET","POST"])
def import_residents():
 if super_guard(): return super_guard()
 c=db()
 c.execute("DELETE FROM import_previews WHERE created_at < datetime('now','-1 day')"); c.commit()
 if request.method=="POST":
  action=request.form.get("action","upload")
  if action in ("confirm","cancel"):
   preview_id=request.form.get("preview_id",type=int)
   preview=c.execute("SELECT * FROM import_previews WHERE id=? AND owner=?",(preview_id,session["user"])).fetchone()
   if not preview:
    c.close(); flash("Import preview expired or not found."); return redirect("/import")
   if action=="cancel":
    c.execute("DELETE FROM import_previews WHERE id=?",(preview_id,)); c.commit(); c.close(); flash("Import cancelled."); return redirect("/import")
   rows=json.loads(preview["rows_json"]); errors=json.loads(preview["errors_json"])
   if errors:
    c.close(); flash("Fix the invalid rows in the source file before importing."); return redirect("/import")
   inserted=0
   for row in rows:
    c.execute("INSERT INTO residents(surname,firstname,year,phone,birth_place,birth_date,status) VALUES(?,?,?,?,?,?, 'active')",
      (row["surname"],row["firstname"],int(row["year"]),row.get("phone",""),row.get("birth_place",""),row.get("birth_date","")))
    inserted+=1
   audit_event(c,"residents.imported",f"filename={preview['filename']}; imported={inserted}; history_not_imported=true")
   c.execute("DELETE FROM import_previews WHERE id=?",(preview_id,)); c.commit(); c.close()
   flash(f"Imported {inserted} residents. No past rotations were invented or imported.")
   return redirect("/residents")
  upload=request.files.get("file")
  if not upload or not upload.filename:
   c.close(); flash("Choose a file first."); return redirect("/import")
  filename=os.path.basename(upload.filename); extension=os.path.splitext(filename)[1].lower()
  allowed={".csv",".xlsx",".xls",".docx",".doc",".pdf"}
  if extension not in allowed:
   c.close(); flash("Supported formats: CSV, XLS/XLSX, DOC/DOCX and text-based PDF."); return redirect("/import")
  staged=None
  try:
   with tempfile.NamedTemporaryFile(prefix="rotation_import_",suffix=extension,dir=os.path.dirname(os.path.abspath(DB)),delete=False) as temp:
    staged=temp.name; upload.save(staged)
   rows=parse_import_file(staged,extension)
   errors=[]; seen=set()
   for row in rows:
    row_errors=[]
    surname=row.get("surname","").strip(); firstname=row.get("firstname","").strip()
    if not surname or not firstname: row_errors.append("Surname and first name are required.")
    try:
     year=int(float(row.get("year","")))
     if year not in (1,2,3,4): raise ValueError()
     row["year"]=year
    except (ValueError,TypeError): row_errors.append("Year must be 1, 2, 3 or 4.")
    row["surname"]=surname; row["firstname"]=firstname
    key=(surname.casefold(),firstname.casefold(),row.get("year"))
    if key in seen: row_errors.append("Duplicate resident row in this file.")
    seen.add(key)
    exists=c.execute("SELECT 1 FROM residents WHERE lower(surname)=lower(?) AND lower(firstname)=lower(?) AND year=?",(surname,firstname,row.get("year",0))).fetchone()
    if exists: row_errors.append("Resident with same name and year already exists.")
    if row_errors: errors.append({"row":row.get("row_number"),"message":" ".join(row_errors)})
   rows.sort(key=lambda row:(row.get("year",99),row.get("surname","").casefold(),row.get("firstname","").casefold()))
   c.execute("DELETE FROM import_previews WHERE created_at < datetime('now','-1 day')")
   c.execute("INSERT INTO import_previews(owner,rows_json,errors_json,filename) VALUES(?,?,?,?)",(session["user"],json.dumps(rows,ensure_ascii=False),json.dumps(errors,ensure_ascii=False),filename))
   preview_id=c.execute("SELECT last_insert_rowid()").fetchone()[0]; c.commit()
   preview=c.execute("SELECT * FROM import_previews WHERE id=?",(preview_id,)).fetchone(); c.close()
   return page("""<section><h3>{{t('import')}} — {{t('preview')}}</h3><p>File: {{filename}} — {{rows|length}} rows. Past stages/history will not be fabricated.</p>{% if errors %}<p class="bad">Validation errors: {{errors|length}}. Correct the source file and upload again; no rows can be imported while errors remain.</p>{% endif %}<div class="wrap"><table><tr><th>Row</th><th>Surname</th><th>First name</th><th>Year</th><th>Phone</th><th>Validation</th></tr>{% for row in rows %}<tr><td>{{row.row_number}}</td><td>{{row.surname}}</td><td>{{row.firstname}}</td><td>{{row.year}}</td><td>{{row.phone or ''}}</td><td>{% for e in errors if e.row==row.row_number %}<span class="bad">{{e.message}}</span>{% else %}<span class="good">OK</span>{% endfor %}</td></tr>{% endfor %}</table></div><form method="post"><input type="hidden" name="preview_id" value="{{preview_id}}"><button name="action" value="confirm" {% if errors %}disabled{% endif %}>{{t('confirm_import')}}</button> <button name="action" value="cancel">{{t('cancel')}}</button></form></section>""",filename=filename,rows=rows,errors=errors,preview_id=preview_id)
  except Exception as exc:
   c.close(); flash("Could not read/validate the file: "+str(exc)[:250]); return redirect("/import")
  finally:
   if staged and os.path.exists(staged): os.remove(staged)
 c.close()
 return page("""<section><h3>{{t('import')}}</h3><p>{{t('import_help')}} Supported: CSV, XLS/XLSX, DOC/DOCX and text-based PDF.</p><form method="post" enctype="multipart/form-data"><label>{{t('file')}}</label><input type="file" name="file" accept=".csv,.xls,.xlsx,.doc,.docx,.pdf" required><button>{{t('upload_preview')}}</button></form></section>""")
@app.get("/photos/<filename>")
def resident_photo(filename):
 if guard(): return redirect("/login")
 safe=secure_filename(filename)
 if safe!=filename or not safe.startswith("resident_") or os.path.splitext(safe)[1].lower() not in (".png",".jpg",".jpeg",".webp"): return ("Not found",404)
 directory=os.path.join(os.path.dirname(os.path.abspath(DB)),"resident_photos")
 return send_from_directory(directory,safe)
@app.route("/profile/<int:rid>",methods=["GET","POST"])
def resident_profile(rid):
 if guard(): return redirect("/login")
 c=db(); r=c.execute("SELECT * FROM residents WHERE id=?",(rid,)).fetchone()
 if not r: c.close(); return ("Resident not found",404)
 if request.method=="POST":
  if session.get("role")!="super_admin": c.close(); return ("Forbidden — Super Admin only",403)
  photo_path=request.form.get("photo_path","").strip()
  photo_file=request.files.get("photo")
  if photo_file and photo_file.filename:
   ext=os.path.splitext(secure_filename(photo_file.filename))[1].lower()
   if ext not in (".png",".jpg",".jpeg",".webp"):
    c.close(); flash("Photo must be PNG, JPG or WEBP."); return redirect("/profile/"+str(rid))
   photo_bytes=photo_file.stream.read(4*1024*1024+1); photo_file.stream.seek(0)
   if len(photo_bytes)>4*1024*1024:
    c.close(); flash("Photo must be 4 MB or smaller."); return redirect("/profile/"+str(rid))
   valid_image=(ext==".png" and photo_bytes.startswith(b"\x89PNG\r\n\x1a\n")) or (ext in (".jpg",".jpeg") and photo_bytes.startswith(b"\xff\xd8\xff")) or (ext==".webp" and len(photo_bytes)>12 and photo_bytes.startswith(b"RIFF") and photo_bytes[8:12]==b"WEBP")
   if not valid_image:
    c.close(); flash("The uploaded file is not a valid PNG/JPG/WEBP image."); return redirect("/profile/"+str(rid))
   photo_dir=os.path.join(os.path.dirname(os.path.abspath(DB)),"resident_photos"); os.makedirs(photo_dir,exist_ok=True)
   photo_name="resident_"+str(rid)+"_"+str(int(datetime.now().timestamp()))+ext
   photo_file.save(os.path.join(photo_dir,photo_name)); photo_path="/photos/"+photo_name
  c.execute("UPDATE residents SET surname=?,firstname=?,birth_place=?,birth_date=?,photo_path=?,phone=? WHERE id=?",
   (request.form.get("surname",r["surname"]).strip(),request.form.get("firstname",r["firstname"]).strip(),request.form.get("birth_place","").strip(),request.form.get("birth_date",""),photo_path,request.form.get("phone","").strip(),rid))
  audit_event(c,"resident.profile_updated",f"resident_id={rid}; name={request.form.get('surname',r['surname']).strip()} {request.form.get('firstname',r['firstname']).strip()}; photo_uploaded={bool(photo_file and photo_file.filename)}")
  c.commit(); r=c.execute("SELECT * FROM residents WHERE id=?",(rid,)).fetchone(); flash(tr("done"))
 history_rows=c.execute("SELECT h.*,t.name terrain FROM history h JOIN terrains t ON t.id=h.terrain_id WHERE h.resident_id=? ORDER BY h.id DESC",(rid,)).fetchall()
 assignment_rows=c.execute("SELECT a.status,p.name period,p.year_label,t.name terrain FROM assignments a JOIN periods p ON p.id=a.period_id JOIN terrains t ON t.id=a.terrain_id WHERE a.resident_id=? ORDER BY p.year_label DESC,p.id",(rid,)).fetchall()
 objectives=c.execute("SELECT o.*,t.name terrain FROM objectives o JOIN terrains t ON t.id=o.terrain_id ORDER BY o.study_year,t.name").fetchall()
 exam_rows=c.execute("SELECT * FROM exam_records WHERE resident_id=? ORDER BY study_year,module",(rid,)).fetchall()
 done={x[0] for x in c.execute("SELECT terrain_id FROM history WHERE resident_id=? UNION SELECT terrain_id FROM assignments WHERE resident_id=? AND status='confirmed'",(rid,rid)).fetchall()}
 terrains=c.execute("SELECT * FROM terrains ORDER BY CASE WHEN kind='optional' THEN 1 ELSE 0 END,name").fetchall(); c.close()
 return page("""<section><h3>{{r.surname}} {{r.firstname}} — Resident profile / Profil / الملف</h3><p>Year: {{r.year}} · Status: {{r.status}}</p>{% if r.photo_path %}<p><img src="{{r.photo_path}}" alt="Resident photo" style="max-width:140px;max-height:140px"></p>{% endif %}<form method="post" enctype="multipart/form-data"><label>{{t('surname')}}</label><input name="surname" value="{{r.surname}}" required><label>{{t('firstname')}}</label><input name="firstname" value="{{r.firstname}}" required><label>Birth place / Lieu de naissance / مكان الميلاد</label><input name="birth_place" value="{{r.birth_place or ''}}"><label>Birth date / Date de naissance / تاريخ الميلاد</label><input type="date" name="birth_date" value="{{r.birth_date or ''}}"><label>Phone / Téléphone / الهاتف</label><input name="phone" value="{{r.phone or ''}}"><label>Photo URL/path / Photo / رابط الصورة</label><input name="photo_path" value="{{r.photo_path or ''}}"><label>Upload photo (PNG/JPG/WEBP, max 4 MB)</label><input type="file" name="photo" accept="image/png,image/jpeg,image/webp"><button>Save / Enregistrer / حفظ</button></form><p><a href="/exams?resident={{r.id}}">Exams / Examens / الامتحانات</a> · <a href="/dems">DEMS archive</a></p></section><section><h3>Terrain progress / Avancement / تقدم التربصات</h3><div class="wrap"><table><tr><th>Terrain</th><th>Status</th></tr>{% for t in terrains %}<tr><td>{{t.name}}</td><td class="{{'bad' if t.id in done else 'good'}}">{{'Completed / Effectué / مكتمل' if t.id in done else 'Remaining / À faire / متبقٍ'}}</td></tr>{% endfor %}</table></div></section><section><h3>Assignments and history / Affectations et historique / التوزيعات والتاريخ</h3>{% for a in assignment_rows %}<p>{{a.year_label}} — {{a.period}} — {{a.terrain}} ({{a.status}})</p>{% endfor %}{% for h in history_rows %}<p>{{h.year_label}} — {{h.period}} — {{h.terrain}} — {{h.date_done}}</p>{% endfor %}</section><section><h3>Exam scores / Notes d’examen / علامات الامتحان</h3><div class="wrap"><table><tr><th>Study year</th><th>Module</th><th>Theory</th><th>Practical</th></tr>{% for e in exam_rows %}<tr><td>{{e.study_year}}</td><td>{{e.module}}</td><td>{{e.theory}}/20</td><td>{{e.practical}}/20</td></tr>{% else %}<tr><td colspan="4">{{t('none')}}</td></tr>{% endfor %}</table></div></section><section><h3>Objectives / Objectifs / الأهداف</h3>{% for o in objectives %}<p>Year {{o.study_year}} — {{o.terrain}}: {{o.objective}}</p>{% else %}<p>{{t('none')}}</p>{% endfor %}</section>""",r=r,terrains=terrains,done=done,assignment_rows=assignment_rows,history_rows=history_rows,objectives=objectives,exam_rows=exam_rows)
@app.route("/objectives",methods=["GET","POST"])
def manage_objectives():
 if super_guard(): return super_guard()
 c=db()
 if request.method=="POST":
  tid=int(request.form["terrain"]); sy=int(request.form["study_year"]); obj=request.form["objective"].strip()
  if obj:
   c.execute("INSERT INTO objectives(terrain_id,study_year,objective) VALUES(?,?,?)",(tid,sy,obj))
   audit_event(c,"objective.created",f"terrain_id={tid}; study_year={sy}")
   c.commit(); flash(tr("done"))
 ts=c.execute("SELECT * FROM terrains WHERE active=1 ORDER BY name").fetchall()
 rows=c.execute("SELECT o.*,t.name terrain FROM objectives o JOIN terrains t ON t.id=o.terrain_id ORDER BY study_year,t.name").fetchall(); c.close()
 return page("""<section><h3>{{t('objectives')}}</h3><form method="post"><label>{{t('terrain')}}</label><select name="terrain">{% for t in ts %}<option value="{{t.id}}">{{t.name}}</option>{% endfor %}</select><label>{{t('study_year')}}</label><select name="study_year">{% for y in range(1,5) %}<option>{{y}}</option>{% endfor %}</select><label>{{t('objective')}}</label><input name="objective" required><button>{{t('save')}}</button></form></section><section>{% for o in rows %}<p>Year {{o.study_year}} — {{o.terrain}}: {{o.objective}}</p>{% else %}<p>{{t('none')}}</p>{% endfor %}</section>""",ts=ts,rows=rows)
@app.route("/exams",methods=["GET","POST"])
def exams():
 if guard(): return redirect("/login")
 c=db()
 if request.method=="POST":
  action=request.form.get("action","record"); rid=int(request.form["resident"]); sy=int(request.form["study_year"])
  resident=c.execute("SELECT * FROM residents WHERE id=?",(rid,)).fetchone()
  if not resident:
   flash("Resident not found")
  elif action=="record":
   module=request.form["module"].strip(); theory=float(request.form["theory"]); practical=float(request.form["practical"])
   if sy not in (1,2,3,4) or not module or not (0<=theory<=20 and 0<=practical<=20):
    flash("Module and marks from 0 to 20 are required")
   else:
    existing=c.execute("SELECT id FROM exam_records WHERE resident_id=? AND study_year=? AND lower(module)=lower(?)",(rid,sy,module)).fetchone()
    if existing:
     c.execute("UPDATE exam_records SET theory=?,practical=?,created_at=CURRENT_TIMESTAMP WHERE id=?",(theory,practical,existing["id"]))
     audit_event(c,"exam.updated",f"resident_id={rid}; year={sy}; module={module}")
    else:
     c.execute("INSERT INTO exam_records(resident_id,study_year,module,theory,practical) VALUES(?,?,?,?,?)",(rid,sy,module,theory,practical))
     audit_event(c,"exam.recorded",f"resident_id={rid}; year={sy}; module={module}")
    c.commit(); flash(tr("done"))
  elif action=="evaluate_first_year" and request.form.get("all_modules_confirmed")!="yes":
   flash("Confirm that all first-year module results have been entered before evaluating progression.")
  elif action=="evaluate_first_year":
   if session.get("role")!="super_admin": c.close(); return ("Forbidden — Super Admin only",403)
   records=c.execute("SELECT theory,practical FROM exam_records WHERE resident_id=? AND study_year=1",(rid,)).fetchall()
   if not records:
    flash("Enter first-year exam modules before evaluation")
   else:
    average=sum((x["theory"]+x["practical"])/2 for x in records)/len(records)
    passed=average>=10 and all(x["theory"]>=10 and x["practical"]>=10 for x in records)
    c.execute("INSERT INTO decisions(details,decision,reason,actor) VALUES(?,?,?,?)",(f"{resident['surname']} {resident['firstname']} — first-year exams","Passed" if passed else "Failed",f"Average={average:.2f}/20; all theory/practical marks >=10: {all(x['theory']>=10 and x['practical']>=10 for x in records)}",session["user"]))
    audit_event(c,"exam.first_year_evaluated",f"resident_id={rid}; average={average:.2f}; passed={passed}")
    if passed and resident["year"]==1:
     c.execute("UPDATE residents SET year=2 WHERE id=?",(rid,))
     audit_event(c,"resident.year_advanced",f"resident_id={rid}; from=1; to=2")
    c.commit(); flash(("Passed; resident advanced to year 2." if passed else "Failed: average must be at least 10/20 and every theory/practical mark must be at least 10/20"))
  elif action=="approve_advance":
   if session.get("role")!="super_admin": c.close(); return ("Forbidden — Super Admin only",403)
   if sy not in (2,3) or resident["year"]!=sy:
    flash("Only an authorized year 2 or 3 progression decision is valid here")
   else:
    c.execute("UPDATE residents SET year=? WHERE id=?",(sy+1,rid))
    c.execute("INSERT INTO decisions(details,decision,reason,actor) VALUES(?,?,?,?)",(f"{resident['surname']} {resident['firstname']} — year {sy}","Approved","Progression approved by logged-in administrator",session["user"]))
    audit_event(c,"resident.year_advanced",f"resident_id={rid}; from={sy}; to={sy+1}")
    c.commit(); flash(tr("done"))
 rows=c.execute("SELECT e.*,r.surname,r.firstname FROM exam_records e JOIN residents r ON r.id=e.resident_id ORDER BY e.created_at DESC,e.id DESC").fetchall()
 rs=c.execute("SELECT * FROM residents WHERE status='active' ORDER BY year DESC,surname").fetchall()
 selected=request.args.get("resident",type=int)
 c.close()
 return page("""<section><h3>{{t('exams')}}</h3><form method="post"><input type="hidden" name="action" value="record"><label>Resident</label><select name="resident">{% for r in rs %}<option value="{{r.id}}" {% if selected==r.id %}selected{% endif %}>{{r.year}} — {{r.surname}} {{r.firstname}}</option>{% endfor %}</select><label>Study year</label><select name="study_year">{% for y in range(1,5) %}<option>{{y}}</option>{% endfor %}</select><label>{{t('module')}}</label><input name="module" required><div class="grid"><div><label>{{t('theory')}}</label><input type="number" name="theory" min="0" max="20" step="0.01" required></div><div><label>{{t('practical')}}</label><input type="number" name="practical" min="0" max="20" step="0.01" required></div></div><button>Record exam / Enregistrer / تسجيل</button></form></section><section><h4>Evaluate first year / Évaluer la 1re année / تقييم السنة الأولى</h4><form method="post"><input type="hidden" name="action" value="evaluate_first_year"><label>Resident</label><select name="resident">{% for r in rs if r.year==1 %}<option value="{{r.id}}">{{r.surname}} {{r.firstname}}</option>{% endfor %}</select><input type="hidden" name="study_year" value="1"><label><input type="checkbox" name="all_modules_confirmed" value="yes" required> Confirm all module results are entered / Confirmer toutes les notes / تأكيد إدخال جميع العلامات</label><button>Evaluate and advance if eligible</button></form><h4>Approve progression (years 2–3)</h4><form method="post"><input type="hidden" name="action" value="approve_advance"><label>Resident</label><select name="resident">{% for r in rs if r.year in [2,3] %}<option value="{{r.id}}">{{r.year}} — {{r.surname}} {{r.firstname}}</option>{% endfor %}</select><label>Study year</label><select name="study_year"><option>2</option><option>3</option></select><button>Approve progression</button></form></section><section><div class="wrap"><table><tr><th>Resident</th><th>Year</th><th>Module</th><th>Theory</th><th>Practical</th></tr>{% for e in rows %}<tr><td>{{e.surname}} {{e.firstname}}</td><td>{{e.study_year}}</td><td>{{e.module}}</td><td>{{e.theory}}</td><td>{{e.practical}}</td></tr>{% else %}<tr><td colspan="5">{{t('none')}}</td></tr>{% endfor %}</table></div></section>""",rows=rows,rs=rs,selected=selected)
@app.route("/dems",methods=["GET","POST"])
def dems():
 if super_guard(): return super_guard()
 c=db()
 if request.method=="POST":
  rid=int(request.form["resident"]); success_date=request.form.get("success_date","").strip()
  r=c.execute("SELECT * FROM residents WHERE id=? AND year=4 AND status='active'",(rid,)).fetchone()
  if not r or not success_date:
   flash("Only an active year-4 resident with a DEMS success date can be archived.")
  else:
   hist=c.execute("SELECT h.*,t.name terrain FROM history h JOIN terrains t ON t.id=h.terrain_id WHERE h.resident_id=?",(rid,)).fetchall()
   asgs=c.execute("SELECT a.*,p.name period,p.year_label,t.name terrain FROM assignments a JOIN periods p ON p.id=a.period_id JOIN terrains t ON t.id=a.terrain_id WHERE a.resident_id=?",(rid,)).fetchall()
   exams_snapshot=c.execute("SELECT * FROM exam_records WHERE resident_id=? ORDER BY study_year,module",(rid,)).fetchall()
   profile={k:r[k] for k in r.keys()}
   c.execute("INSERT INTO dems_archive(resident_id,success_date,profile_json,history_json) VALUES(?,?,?,?)",(rid,success_date,json.dumps(profile,ensure_ascii=False),json.dumps({"history":[dict(x) for x in hist],"assignments":[dict(x) for x in asgs],"exams":[dict(x) for x in exams_snapshot]},ensure_ascii=False)))
   c.execute("UPDATE residents SET status='graduated',dems_status='success' WHERE id=?",(rid,))
   audit_event(c,"dems.archived",f"resident_id={rid}; success_date={success_date}")
   c.commit(); flash("Resident archived; original records retained.")
 residentsrow_numbers=c.execute("SELECT * FROM residents WHERE year=4 AND status='active' ORDER BY surname").fetchall()
 archiverow_numbers=c.execute("SELECT d.*,r.surname,r.firstname FROM dems_archive d JOIN residents r ON r.id=d.resident_id ORDER BY d.id DESC").fetchall()
 c.close()
 return page("""<section><h3>{{t('dems')}}</h3><form method="post"><label>Year-4 resident</label><select name="resident">{% for r in residentsrow_numbers %}<option value="{{r.id}}">{{r.surname}} {{r.firstname}}</option>{% endfor %}</select><label>{{t('success_date')}}</label><input type="date" name="success_date" required><button>{{t('archive')}}</button></form><p>{{t('archive_note')}}</p></section><section><h4>Archived graduates</h4>{% for a in archiverow_numbers %}<p>{{a.surname}} {{a.firstname}} — DEMS success: {{a.success_date}} — archived {{a.archived_at}}</p>{% else %}<p>{{t('none')}}</p>{% endfor %}</section>""",residentsrow_numbers=residentsrow_numbers,archiverow_numbers=archiverow_numbers)
@app.get("/export")
def export():
 if super_guard():return super_guard()
 c=db(); out=io.StringIO(); w=csv.writer(out)
 for table in ["residents","terrains","periods","capacities","assignments","history","decisions","exam_records","objectives","dems_archive","audit"]:
  w.writerow([table])
  w.writerow([x[1] for x in c.execute('PRAGMA table_info("'+table+'")')])
  for row in c.execute('SELECT * FROM "'+table+'"'):w.writerow(list(row))
 c.close(); f=io.BytesIO(("\ufeff"+out.getvalue()).encode("utf-8")); return send_file(f,mimetype="text/csv",as_attachment=True,download_name="rotation_export.csv")
@app.get("/backup")
def backup():
 if super_guard(): return super_guard()
 directory=os.path.dirname(os.path.abspath(DB))
 target=os.path.join(directory,"rotation_backup_download.db")
 source=sqlite3.connect(DB,timeout=20)
 destination=sqlite3.connect(target)
 try:
  source.backup(destination)
  destination.commit()
 finally:
  destination.close(); source.close()
 ctype="application/octet-stream"
 return send_file(target,mimetype=ctype,as_attachment=True,download_name="rotation_backup.db")
@app.route("/restore",methods=["GET","POST"])
def restore():
 if super_guard(): return super_guard()
 if request.method=="POST":
  uploaded=request.files.get("backup_file")
  if not uploaded or not uploaded.filename or not uploaded.filename.lower().endswith((".db",".sqlite",".sqlite3")):
   flash("Choose a valid .db/.sqlite backup file.")
   return redirect("/restore")
  directory=os.path.dirname(os.path.abspath(DB))
  staged=None
  try:
   with tempfile.NamedTemporaryFile(prefix="rotation_restore_",suffix=".db",dir=directory,delete=False) as temp:
    staged=temp.name
    uploaded.save(staged)
   check=sqlite3.connect("file:"+staged+"?mode=ro",uri=True,timeout=10)
   integrity=check.execute("PRAGMA integrity_check").fetchone()[0]
   tables={row[0] for row in check.execute("SELECT name FROM sqlite_master WHERE type='table'")}
   check.close()
   required={"residents","terrains","periods","assignments","history","settings"}
   if integrity!="ok" or not required.issubset(tables):
    raise ValueError("The uploaded file is not a valid Rotation App database backup.")
   timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
   before=os.path.join(directory,"rotation_backup_before_restore_"+timestamp+".db")
   current=sqlite3.connect(DB,timeout=20)
   saved=sqlite3.connect(before)
   try:
    current.backup(saved); saved.commit()
   finally:
    saved.close(); current.close()
   os.replace(staged,DB); staged=None
   app._ready=False
   init()
   c=db(); audit_event(c,"database.restored",f"Restored from uploaded backup; pre-restore backup={os.path.basename(before)}"); c.commit(); c.close()
   flash("Restore completed. A pre-restore backup was saved as "+os.path.basename(before))
  except Exception as exc:
   flash("Restore failed; the current database was not intentionally replaced. Details: "+str(exc)[:250])
  finally:
   if staged and os.path.exists(staged): os.remove(staged)
  return redirect("/restore")
 return page("""<section><h3>{{t('restore')}}</h3><p>{{t('restore_help')}} Upload only a backup made by this app.</p><form method="post" enctype="multipart/form-data"><label>{{t('file')}} (.db/.sqlite)</label><input type="file" name="backup_file" accept=".db,.sqlite,.sqlite3" required><button>{{t('restore')}}</button></form></section>""")
if __name__=="__main__":
 init(); app.run(host="127.0.0.1",port=int(os.environ.get("PORT","5000")),debug=False)
