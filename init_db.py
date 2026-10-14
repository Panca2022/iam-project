import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('database.db')
c = conn.cursor()

c.executescript('''
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT UNIQUE NOT NULL,
    password        TEXT NOT NULL,
    role            TEXT NOT NULL,
    failed_attempts INTEGER DEFAULT 0,
    locked_until    TEXT,
    last_login      TEXT,
    is_active       INTEGER DEFAULT 1,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER,
    username   TEXT,
    action     TEXT NOT NULL,
    target     TEXT,
    ip_address TEXT,
    timestamp  TEXT DEFAULT CURRENT_TIMESTAMP
);
''')

hashed_pw = generate_password_hash("Admin@123")
c.execute(
    "INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
    ("admin", hashed_pw, "admin")
)

conn.commit()
conn.close()
print("Database initialized. Admin: admin / Admin@123")