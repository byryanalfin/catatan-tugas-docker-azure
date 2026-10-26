import hmac
import os
import secrets
from datetime import date
from functools import wraps

import psycopg
from flask import Flask, abort, redirect, render_template, request, session, url_for
from psycopg.rows import dict_row

app = Flask(__name__)
app.config.update(SECRET_KEY=os.environ['APP_SECRET'], MAX_CONTENT_LENGTH=16384,
                  SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

def db():
    return psycopg.connect(host=os.getenv('DB_HOST', 'database'),
        dbname=os.environ['DB_NAME'], user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'], connect_timeout=5, row_factory=dict_row)

def protected(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        auth = request.authorization
        valid_basic = auth and hmac.compare_digest((auth.username or '').encode(), os.environ['APP_USER'].encode()) and hmac.compare_digest((auth.password or '').encode(), os.environ['APP_PASSWORD'].encode())
        if not session.get('logged_in') and not valid_basic:
            return redirect(url_for('login'))
        if request.method == 'POST' and (not session.get('csrf') or not hmac.compare_digest(
                session['csrf'].encode(), request.form.get('csrf', '').encode())):
            abort(400)
        return fn(*args, **kwargs)
    return wrapped

@app.route('/login', methods=['GET', 'POST'])
def login():
    session.setdefault('csrf', secrets.token_hex(32))
    error = None
    if request.method == 'POST':
        if not hmac.compare_digest(session['csrf'].encode(), request.form.get('csrf', '').encode()):
            abort(400)
        if (hmac.compare_digest(request.form.get('username', '').encode(), os.environ['APP_USER'].encode())
                and hmac.compare_digest(request.form.get('password', '').encode(), os.environ['APP_PASSWORD'].encode())):
            session.clear()
            session['logged_in'] = True
            session['csrf'] = secrets.token_hex(32)
            return redirect(url_for('index'))
        error = 'Username atau password tidak sesuai.'
    return render_template('login.html', error=error), 401 if error else 200

@app.post('/logout')
@protected
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.get('/health')
def health():
    try:
        with db() as conn:
            conn.execute('SELECT 1')
        return {'status': 'healthy'}
    except psycopg.Error:
        return {'status': 'unavailable'}, 503

@app.get('/')
@protected
def index():
    session.setdefault('csrf', secrets.token_hex(32))
    with db() as conn:
        tasks = conn.execute('SELECT * FROM tasks ORDER BY done, due_date NULLS LAST, id DESC').fetchall()
    return render_template('index.html', tasks=tasks, today=date.today(),
                           completed=sum(t['done'] for t in tasks))

@app.post('/tasks')
@protected
def create():
    title = request.form.get('title', '').strip()
    course = request.form.get('course', '').strip()
    if not title or len(title) > 150 or not course or len(course) > 100:
        abort(400, 'Judul dan mata kuliah wajib diisi sesuai batas panjang.')
    try:
        due = date.fromisoformat(request.form['due']) if request.form.get('due') else None
    except ValueError:
        abort(400, 'Tanggal tidak valid.')
    with db() as conn:
        conn.execute('INSERT INTO tasks (title, course, due_date) VALUES (%s,%s,%s)', (title, course, due))
    return redirect(url_for('index'))

@app.post('/tasks/<int:task_id>/toggle')
@protected
def toggle(task_id):
    with db() as conn:
        conn.execute('UPDATE tasks SET done = NOT done WHERE id = %s', (task_id,))
    return redirect(url_for('index'))

@app.post('/tasks/<int:task_id>/delete')
@protected
def delete(task_id):
    with db() as conn:
        conn.execute('DELETE FROM tasks WHERE id = %s', (task_id,))
    return redirect(url_for('index'))
