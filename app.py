@app.route('/signin', methods=['POST'])
def signin():
    name = request.form['name']
    password = request.form['password']
    if city.sign_in(name, password):
        return redirect(url_for('success', username=quote(name)))
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
