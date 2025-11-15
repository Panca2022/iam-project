from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from flask import abort


app = Flask(__name__)
app.secret_key = "your_secret_key"

# Helper function to get DB connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    username = session.get('username')
    role = session.get('role')
    return render_template('home.html', username=username, role=role) 

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']  # user/admin

        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                         (username, password, role))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Username already exists!"
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['username'] = user['username']
            session['role'] = user['role']
            # Redirect based on role
            if session['role'] == 'admin':
                return redirect(url_for('admin_page'))
            else:
                return redirect(url_for('user_page'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return render_template('logout.html')

@app.route('/admin')
def admin_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    if session['role'] != 'admin':
        return abort(403)
    
    conn = get_db_connection()
    users = conn.execute("SELECT id, username, role FROM users").fetchall()
    conn.close()
    
    return render_template('admin.html', username=session['username'], users=users)

@app.route('/delete_user/<int:user_id>')
def delete_user(user_id):
    if 'username' not in session or session.get('role') != 'admin':
        return abort(403)  # Forbidden
    
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id = ? AND role != 'admin'", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_page'))

@app.route('/user')
def user_page():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    return render_template('user.html', username=session['username'], role=session['role'])

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000, debug=True)

