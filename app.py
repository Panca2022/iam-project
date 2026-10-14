import os
import re
import sqlite3
from datetime import datetime, timedelta
from functools import wraps

from flask import (Flask, render_template, request, redirect,
                   url_for, session, abort)
from werkzeug.security import generate_password_hash, check_password_hash


# ------------------------------------------------------------------
# 1. App configuration (12-factor: secrets come from env)
# ------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

# 2. Session hardening  (NEW)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,     # JS cannot read the cookie (XSS mitigation)
    SESSION_COOKIE_SAMESITE="Lax",    # CSRF mitigation
    SESSION_COOKIE_SECURE=False,      # flip True when served over HTTPS
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
)

# 3. Brute-force policy (NEW)
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES     = 15


# ------------------------------------------------------------------
# 4. DB helper
# ------------------------------------------------------------------
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


# ------------------------------------------------------------------
# 5. Decorators — clean RBAC (NEW)
# ------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return wrapper


# ------------------------------------------------------------------
# 6. Audit-log helper (NEW)
# ------------------------------------------------------------------
def log_action(action, target=None):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO audit_logs (user_id, username, action, target, ip_address) "
        "VALUES (?, ?, ?, ?, ?)",
        (session.get('user_id'), session.get('username'),
         action, target, request.remote_addr)
    )
    conn.commit()
    conn.close()


# ------------------------------------------------------------------
# 7. Password strength policy (NEW)
# ------------------------------------------------------------------
def validate_password_strength(pw):
    if len(pw) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", pw):
        return False, "Must contain at least one uppercase letter."
    if not re.search(r"[a-z]", pw):
        return False, "Must contain at least one lowercase letter."
    if not re.search(r"\d", pw):
        return False, "Must contain at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=]", pw):
        return False, "Must contain at least one special character."
    return True, ""


# ------------------------------------------------------------------
# 8. Routes
# ------------------------------------------------------------------
@app.route('/')
def home():
    return render_template('home.html',
                           username=session.get('username'),
                           role=session.get('role'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        raw_pw   = request.form['password']
        role     = request.form['role']

        ok, err = validate_password_strength(raw_pw)
        if not ok:
            return render_template('register.html', error=err)

        hashed = generate_password_hash(raw_pw)
        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, hashed, role))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html',
                                   error="Username already exists.")
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=?", (username,)).fetchone()

        # 9. Lockout check (NEW)
        if user and user['locked_until']:
            if datetime.fromisoformat(user['locked_until']) > datetime.now():
                conn.close()
                return render_template(
                    'login.html',
                    error="Account temporarily locked. Try again later.")

        if user and user['is_active'] and check_password_hash(user['password'], password):
            # success → reset counters, stamp last_login
            conn.execute(
                "UPDATE users SET failed_attempts=0, locked_until=NULL, "
                "last_login=? WHERE id=?",
                (datetime.now().isoformat(), user['id']))
            conn.commit()
            conn.close()

            session.permanent = True
            session['user_id']  = user['id']
            session['username'] = user['username']
            session['role']     = user['role']
            log_action("LOGIN_SUCCESS", target=user['username'])

            return redirect(url_for('admin_page')
                            if user['role'] == 'admin'
                            else url_for('user_page'))

        # failure path
        if user:
            attempts = (user['failed_attempts'] or 0) + 1
            lock_until = None
            if attempts >= MAX_FAILED_ATTEMPTS:
                lock_until = (datetime.now()
                              + timedelta(minutes=LOCKOUT_MINUTES)).isoformat()
            conn.execute(
                "UPDATE users SET failed_attempts=?, locked_until=? WHERE id=?",
                (attempts, lock_until, user['id']))
            conn.commit()
        conn.close()

        log_action("LOGIN_FAILED", target=username)
        return render_template('login.html',
                               error="Invalid username or password.")
    return render_template('login.html')


@app.route('/logout')
def logout():
    if 'username' in session:
        log_action("LOGOUT", target=session['username'])
    session.clear()
    return render_template('logout.html')


@app.route('/admin')
@admin_required
def admin_page():
    page     = request.args.get('page', 1, type=int)
    per_page = 10
    offset   = (page - 1) * per_page
    search   = request.args.get('q', '').strip()

    conn = get_db_connection()
    if search:
        users = conn.execute(
            "SELECT id, username, role, is_active, last_login FROM users "
            "WHERE username LIKE ? ORDER BY id LIMIT ? OFFSET ?",
            (f"%{search}%", per_page, offset)).fetchall()
        total = conn.execute(
            "SELECT COUNT(*) FROM users WHERE username LIKE ?",
            (f"%{search}%",)).fetchone()[0]
    else:
        users = conn.execute(
            "SELECT id, username, role, is_active, last_login FROM users "
            "ORDER BY id LIMIT ? OFFSET ?",
            (per_page, offset)).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    logs = conn.execute(
        "SELECT * FROM audit_logs ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()

    total_pages = max(1, (total + per_page - 1) // per_page)
    return render_template('admin.html',
                           username=session['username'],
                           users=users, logs=logs,
                           page=page, total_pages=total_pages,
                           search=search)


@app.route('/delete_user/<int:user_id>')
@admin_required
def delete_user(user_id):
    """Soft delete: deactivate instead of hard-delete."""
    conn = get_db_connection()
    target = conn.execute(
        "SELECT username FROM users WHERE id=?", (user_id,)).fetchone()
    if target and target['username'] == session['username']:
        conn.close()
        return "You cannot deactivate your own account.", 400
    conn.execute(
        "UPDATE users SET is_active=0 WHERE id=? AND role != 'admin'",
        (user_id,))
    conn.commit()
    conn.close()
    log_action("USER_DEACTIVATED", target=str(user_id))
    return redirect(url_for('admin_page'))


@app.route('/user')
@login_required
def user_page():
    return render_template('user.html',
                           username=session['username'],
                           role=session['role'])


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old = request.form['old_password']
        new = request.form['new_password']

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE id=?",
                            (session['user_id'],)).fetchone()

        if not check_password_hash(user['password'], old):
            conn.close()
            return render_template('change_password.html',
                                   error="Current password is incorrect.")

        ok, err = validate_password_strength(new)
        if not ok:
            conn.close()
            return render_template('change_password.html', error=err)

        conn.execute("UPDATE users SET password=? WHERE id=?",
                     (generate_password_hash(new), session['user_id']))
        conn.commit()
        conn.close()
        log_action("PASSWORD_CHANGED", target=session['username'])
        return redirect(url_for('user_page'))
    return render_template('change_password.html')


# 10. Health check (NEW)
@app.route('/health')
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}, 200


# 11. HTTP error handlers
@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403


if __name__ == "__main__":
    app.run(host='0.0.0.0',
            port=int(os.environ.get("PORT", 3000)),
            debug=os.environ.get("FLASK_ENV") != "production")