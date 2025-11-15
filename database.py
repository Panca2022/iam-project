import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('database.db')
c = conn.cursor()

# Create table
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE NOT NULL,
              password TEXT NOT NULL,
              role TEXT NOT NULL)''')

# Add an admin user
hashed_pw = generate_password_hash("admin123")
c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
          ("admin", hashed_pw, "admin"))

conn.commit()
conn.close()
print("Database initialized with admin user!")
