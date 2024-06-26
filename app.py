from flask import Flask, render_template, request, jsonify, redirect, url_for
import hashlib
import sqlite3
from urllib.parse import quote

app = Flask(__name__)

class City:
    def __init__(self, db_name):
        self.db_name = db_name

    def add_user(self, name, password):
        hashed_password = self._hash_password(password)
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, password) VALUES (?, ?)", (name, hashed_password))
            conn.commit()

    def sign_in(self, name, password):
        hashed_password = self._hash_password(password)
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE name = ? AND password = ?", (name, hashed_password))
            return cursor.fetchone() is not None

    def get_user_scores(self, name):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scores WHERE user = ?", (name,))
            return cursor.fetchall()

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

city = City("users.db")

# Initialize database
with sqlite3.connect("users.db") as conn:
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY, password TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS scores (id INTEGER PRIMARY KEY, user TEXT, subject TEXT, score INTEGER)")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['POST'])
def signup():
    name = request.form['name']
    password = request.form['password']
    # Check if the user already exists
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
        existing_user = cursor.fetchone()
        if existing_user:
            return jsonify({'status': 'error', 'message': '使用者已存在，請嘗試其他名稱。'})
    city.add_user(name, password)
    return jsonify({'status': 'success', 'message': f'使用者 {name} 註冊成功！請登入。'})

@app.route('/signin', methods=['POST'])
def signin():
    name = request.form['name']
    password = request.form['password']
    if city.sign_in(name, password):
        return redirect(url_for('user_scores', username=quote(name)))
    else:
        # Check if the user exists and display appropriate error message if not
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
            existing_user = cursor.fetchone()
            if not existing_user:
                message = '該使用者尚未註冊。'
            else:
                message = '無效的名稱或密碼。請重試。'
        return render_template('index.html', login_alert=message)

@app.route('/changepassword', methods=['POST'])
def change_password():
    name = request.form['name']
    old_password = request.form['old_password']
    new_password = request.form['new_password']
    if city.change_password(name, old_password, new_password):
        return jsonify({'status': 'success', 'message': '密碼已成功更改。'})
    else:
        return jsonify({'status': 'error', 'message': '無效的名稱或密碼。密碼更新失敗。'})

@app.route('/success/<username>')
def user_scores(username):
    scores = city.get_user_scores(username)
    return render_template('scores.html', username=username, scores=scores)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=4000)
