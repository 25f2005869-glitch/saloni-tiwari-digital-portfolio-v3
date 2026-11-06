import os, json, sqlite3, secrets
from pathlib import Path
from functools import wraps
from hmac import compare_digest
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE=Path(__file__).resolve().parent
DATA_DIR=Path(os.environ.get('DATA_DIR', BASE))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB=DATA_DIR/'portfolio.db'
UPLOAD=DATA_DIR/'uploads'
UPLOAD.mkdir(parents=True,exist_ok=True)
app=Flask(__name__)
app.secret_key=os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config.update(MAX_CONTENT_LENGTH=40*1024*1024, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE','0')=='1')
ADMIN_USER=os.environ.get('ADMIN_USERNAME','saloni')
ADMIN_PASSWORD=os.environ.get('ADMIN_PASSWORD','')
ALLOWED={'png','jpg','jpeg','webp','gif','mp4','webm','pdf','ppt','pptx','pbix'}
TABLES={
 'projects':['title','category','description','tools','image','github_url','demo_url','published'],
 'certificates':['title','organization','category','file','description','issue_date','status','published'],
 'education':['title','institution','level','status','details','published'],
 'skills':['title','category','level','details','published'],
 'achievements':['title','organization','date','details','url','published'],
 'journey':['title','category','status','date','details','published'],
 'media':['title','category','file','description','published']}
LABELS={'projects':'Projects','certificates':'Certificates','education':'Education','skills':'Skills','achievements':'Achievements','journey':'Learning Journey','media':'Media Gallery'}

def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init_db():
 c=db()
 for table,fields in TABLES.items():
  defs=[]
  for f in fields:
   typ='INTEGER' if f=='published' else 'TEXT'
   defs.append(f'"{f}" {typ}'+(" DEFAULT 1" if f=='published' else " DEFAULT ''"))
  c.execute(f'CREATE TABLE IF NOT EXISTS {table} (id INTEGER PRIMARY KEY AUTOINCREMENT, {", ".join(defs)})')
  if c.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]==0:
   seed=BASE/f'seed_{table}.json'
   if seed.exists():
    rows=json.loads(seed.read_text(encoding='utf-8'))
    for row in rows:
     keys=[k for k in fields if k in row]
     c.execute(f'INSERT INTO {table} ({",".join(keys)}) VALUES ({",".join("?" for _ in keys)})',[row[k] for k in keys])
 c.commit(); c.close()
init_db()

def csrf():
 if 'csrf' not in session: session['csrf']=secrets.token_urlsafe(24)
 return session['csrf']
app.jinja_env.globals['csrf_token']=csrf

def verify_csrf():
 if request.form.get('_csrf')!=session.get('csrf'): abort(400,'Invalid form token')

def login_required(fn):
 @wraps(fn)
 def wrapper(*a,**kw):
  if not session.get('admin'): return redirect(url_for('login',next=request.path))
  return fn(*a,**kw)
 return wrapper

def rows(table,where='published=1',params=()):
 c=db(); result=c.execute(f'SELECT * FROM {table} WHERE {where} ORDER BY id DESC',params).fetchall(); c.close(); return result

@app.route('/')
def home():
 data={t:rows(t) for t in TABLES}
 return render_template('home.html',data=data)

@app.route('/login',methods=['GET','POST'])
def login():
 if not ADMIN_PASSWORD: return render_template('login.html',setup=True)
 if request.method=='POST':
  verify_csrf(); u=request.form.get('username',''); p=request.form.get('password','')
  if u==ADMIN_USER and compare_digest(ADMIN_PASSWORD,p):
   session.clear(); session['admin']=True; session['csrf']=secrets.token_urlsafe(24); return redirect(request.args.get('next') or url_for('admin'))
  flash('Username or password is incorrect.','error')
 return render_template('login.html',setup=False)

@app.route('/logout',methods=['POST'])
@login_required
def logout():
 verify_csrf(); session.clear(); return redirect(url_for('home'))

@app.route('/admin')
@login_required
def admin():
 counts={t:db_count(t) for t in TABLES}
 return render_template('admin.html',counts=counts,labels=LABELS)

def db_count(t):
 c=db(); n=c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]; c.close(); return n

@app.route('/admin/<table>')
@login_required
def manage(table):
 if table not in TABLES: abort(404)
 c=db(); items=[dict(r) for r in c.execute(f'SELECT * FROM {table} ORDER BY id DESC').fetchall()]; c.close()
 return render_template('manage.html',table=table,label=LABELS[table],fields=TABLES[table],items=items)

@app.route('/admin/<table>/save',methods=['POST'])
@login_required
def save(table):
 if table not in TABLES: abort(404)
 verify_csrf(); fields=TABLES[table]; rid=request.form.get('id','').strip(); values={f:request.form.get(f,'').strip() for f in fields}
 values['published']=1 if request.form.get('published')=='on' else 0
 if table in ('projects','certificates','media'):
  file=request.files.get('upload')
  if file and file.filename:
   ext=file.filename.rsplit('.',1)[-1].lower() if '.' in file.filename else ''
   if ext not in ALLOWED: flash('File type not allowed.','error'); return redirect(url_for('manage',table=table))
   name=secure_filename(file.filename); name=f'{secrets.token_hex(8)}_{name}'; file.save(UPLOAD/name)
   values['image' if table=='projects' else 'file']='uploads/'+name
  elif rid:
   c=db(); old=c.execute(f'SELECT * FROM {table} WHERE id=?',(rid,)).fetchone(); c.close()
   target='image' if table=='projects' else 'file'
   if old and not values.get(target): values[target]=old[target]
 keys=list(values); c=db()
 if rid:
  c.execute(f'UPDATE {table} SET '+','.join(f'"{k}"=?' for k in keys)+' WHERE id=?',[values[k] for k in keys]+[rid])
 else:
  c.execute(f'INSERT INTO {table} ('+','.join(f'"{k}"' for k in keys)+') VALUES ('+','.join('?' for _ in keys)+')',[values[k] for k in keys])
 c.commit(); c.close(); flash('Record saved.','success'); return redirect(url_for('manage',table=table))

@app.route('/admin/<table>/<int:rid>/delete',methods=['POST'])
@login_required
def delete(table,rid):
 if table not in TABLES: abort(404)
 verify_csrf(); c=db(); c.execute(f'DELETE FROM {table} WHERE id=?',(rid,)); c.commit(); c.close(); flash('Record deleted.','success'); return redirect(url_for('manage',table=table))

@app.route('/admin/export')
@login_required
def export_data():
 c=db(); payload={t:[dict(r) for r in c.execute(f'SELECT * FROM {t}').fetchall()] for t in TABLES}; c.close()
 from flask import Response
 return Response(json.dumps(payload,ensure_ascii=False,indent=2),mimetype='application/json',headers={'Content-Disposition':'attachment; filename=saloni-portfolio-backup.json'})

@app.route('/admin/import',methods=['POST'])
@login_required
def import_data():
 verify_csrf(); f=request.files.get('backup')
 if not f: flash('Choose a backup JSON file.','error'); return redirect(url_for('admin'))
 try:
  payload=json.load(f)
  c=db()
  for t,fields in TABLES.items():
   for row in payload.get(t,[]):
    vals={k:row.get(k,'') for k in fields}; keys=list(vals)
    c.execute(f'INSERT INTO {t} ({",".join(keys)}) VALUES ({",".join("?" for _ in keys)})',[vals[k] for k in keys])
  c.commit(); c.close(); flash('Backup imported as additional records; existing records were not overwritten.','success')
 except Exception as e: flash('Could not import backup: '+str(e),'error')
 return redirect(url_for('admin'))

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
 from flask import send_from_directory
 if not session.get('admin'):
  rel='uploads/'+filename
  c=db()
  allowed=False
  for table in ('projects','certificates','media'):
   col='image' if table=='projects' else 'file'
   if c.execute(f'SELECT 1 FROM {table} WHERE {col}=? AND published=1 LIMIT 1',(rel,)).fetchone():
    allowed=True; break
  c.close()
  if not allowed: abort(404)
 return send_from_directory(UPLOAD, filename)

@app.route('/health')
def health(): return {'status':'ok','database':DB.exists()}

if __name__=='__main__':
 app.run(host='127.0.0.1',port=int(os.environ.get('PORT',5000)),debug=False)
