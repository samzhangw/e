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

    def change_password(self, name, old_password, new_password):
        if self.sign_in(name, old_password):
            hashed_new_password = self._hash_password(new_password)
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET password = ? WHERE name = ?", (hashed_new_password, name))
                conn.commit()
            return True
        return False

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

city = City("users.db")

# Initialize database
with sqlite3.connect("users.db") as conn:
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY, password TEXT)")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['POST'])
def signup():
    name = request.form['name']
    password = request.form['password']
    # 檢查用戶是否已經存在
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
        return redirect(url_for('success', username=quote(name)))
    else:
        # 檢查用戶是否存在，如果不存在則顯示未註冊的錯誤訊息
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
def success(username):
    return render_template('welcome.html', username=username)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=4000)

