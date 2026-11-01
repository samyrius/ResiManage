"""Import data from the older rotation_app SQLite schema without modifying it.
Run only after copying old rotation.db as legacy_rotation.db into this folder.
"""
import os, sqlite3, shutil, unicodedata
HERE=os.path.dirname(os.path.abspath(__file__))
OLD=os.path.join(HERE,'legacy_rotation.db')
NEW=os.path.join(HERE,'rotation.db')
if not os.path.exists(OLD):
    raise SystemExit('Fichier legacy_rotation.db absent. Copiez une SAUVEGARDE de l’ancienne base sous ce nom.')
if os.path.exists(NEW):
    con=sqlite3.connect(NEW)
    tables={r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    if 'residents' in tables and con.execute('select count(*) from residents').fetchone()[0]:
        raise SystemExit('La nouvelle base contient déjà des données. Import arrêté pour éviter les doublons.')
    con.close()
old=sqlite3.connect(f'file:{OLD}?mode=ro',uri=True); old.row_factory=sqlite3.Row
new=sqlite3.connect(NEW); new.row_factory=sqlite3.Row
# This file is run after app.py has initialized the new schema.
def tables(c): return {r[0] for r in c.execute("select name from sqlite_master where type='table'")}
ot=tables(old)
if 'residents' not in ot or 'terrains' not in ot: raise SystemExit('Le schéma de l’ancienne base n’est pas reconnu; aucune modification faite.')
new.execute('PRAGMA foreign_keys=ON')
# Keep original names intact in surname; empty firstname avoids inventing corrections.
rmap={}; tmap={}
for r in old.execute('select * from residents'):
    keys=set(r.keys()); name=(r['name'] if 'name' in keys else '').strip()
    if not name: continue
    got=new.execute('select id from residents where lower(trim(surname||\' \'||firstname))=lower(?)',(name,)).fetchone()
    if got: rid=got['id']
    else:
        year=1
        try:
            new.execute('insert into residents(surname,firstname,year,status) values(?,?,?,?)',(name,'',year,'active')); rid=new.execute('select last_insert_rowid()').fetchone()[0]
        except sqlite3.IntegrityError: continue
    rmap[r['id']]=rid
for t in old.execute('select * from terrains'):
    name=t['name'].strip(); got=new.execute('select id from terrains where lower(name)=lower(?)',(name,)).fetchone()
    if got: tid=got['id']
    else:
        try:new.execute('insert into terrains(name,kind) values(?,?)',(name,'basic'));tid=new.execute('select last_insert_rowid()').fetchone()[0]
        except sqlite3.IntegrityError:continue
    tmap[t['id']]=tid
# Existing assignments are imported as historical records, not live assignments,
# because their period/year may refer to the old planning cycle.
if 'assignments' in ot:
    cols={r[1] for r in old.execute('pragma table_info(assignments)')}
    if {'resident_id','terrain_id','period'} <= cols:
        for a in old.execute('select * from assignments'):
            if a['resident_id'] not in rmap or a['terrain_id'] not in tmap: continue
            period=str(a['period'] or 'Période ancienne')
            year='Ancien planning'
            new.execute('insert into periods(year_label,name) values(?,?) on conflict(year_label,name) do nothing',(year,period))
            new.execute('insert into history(resident_id,terrain_id,year_label,period,date_done) values(?,?,?,?,?)',(rmap[a['resident_id']],tmap[a['terrain_id']],year,period,''))
if 'stage_history' in ot:
    cols={r[1] for r in old.execute('pragma table_info(stage_history)')}
    if {'resident_id','terrain_id'} <= cols:
        for h in old.execute('select * from stage_history'):
            if h['resident_id'] not in rmap or h['terrain_id'] not in tmap: continue
            year=h['academic_year'] if 'academic_year' in cols and h['academic_year'] else 'Historique importé'
            period=h['period'] if 'period' in cols and h['period'] else 'Non précisée'
            date=h['completion_date'] if 'completion_date' in cols and h['completion_date'] else ''
            new.execute('insert into history(resident_id,terrain_id,year_label,period,date_done) values(?,?,?,?,?)',(rmap[h['resident_id']],tmap[h['terrain_id']],year,period,date))
new.commit(); new.close(); old.close()
print('Import terminé. Ancienne base legacy_rotation.db conservée intacte. Vérifiez les noms et années avant utilisation.')
