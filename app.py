from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "keykey"
DB_PATH = "instance/app.db"

# set up database
def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT,
            age INTEGER,
            bio TEXT,
            profile_picture TEXT
        )''')
        conn.commit()
        conn.close()

@app.before_request
def setup():
    # init only once
    if not hasattr(app, 'db_initialized'):
        init_db()
        app.db_initialized = True

# 2 pages
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('profile'))
    return redirect(url_for('login'))

# register a user
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # grab info
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        # database connection
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # insert into db
        try:
            # commit to db
            c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                      (username, email, password))
            conn.commit()
            conn.close()

            # update user
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))

        # failed to insert
        except sqlite3.IntegrityError:
            flash('Username or email already exists.', 'error')
            return redirect(url_for('register'))


    return render_template('register.html')

# login to account
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # grab user inputted values
        email = request.form['email']
        password = request.form['password']

        # laod db
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()

        # verify credentials
        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            flash('Logged in successfully!', 'success')
            return redirect(url_for('profile'))

        #invalid
        flash('Invalid credentials.', 'error')

    return render_template('login.html')
# profile page
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # only if logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # connect to db
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    user_id = session['user_id']

    if request.method == 'POST':
        # grab/insert relevant info
        name = request.form['name']
        age = request.form['age']
        bio = request.form['bio']
        profile_picture = request.files.get('profile_picture')
        picture_path = f"static/images/{user_id}_profile.jpg"

        # save picture
        if profile_picture:
            profile_picture.save(picture_path)
        else:
            picture_path = "static/images/default.jpg"

        # update changes
        c.execute("UPDATE users SET name = ?, age = ?, bio = ?, profile_picture = ? WHERE id = ?",
                  (name, age, bio, picture_path, user_id))
        conn.commit()

    # load data
    c.execute("SELECT username, email, name, age, bio, profile_picture FROM users WHERE id = ?",
              (user_id,))
    user = c.fetchone()
    conn.close()

    # render and display profile page
    return render_template('profile.html', user=user)


# self explanatory
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
