import requests
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import hashlib
import random
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("APP_SECRET_KEY")
app.config['MYSQL_HOST'] = os.getenv("MYSQL_HOST") #local host
app.config['MYSQL_USER'] = os.getenv("MYSQL_USER") # root
app.config['MYSQL_PASSWORD'] = os.getenv("MYSQL_PASSWORD")
app.config['MYSQL_DB'] = os.getenv("MYSQL_DB") # name of db
API_KEY = os.getenv("API_KEY") # API Jamendo

mysql = MySQL(app)


@app.route('/')
@app.route('/musicwebplayer', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        hash = password + app.secret_key
        hash = hashlib.sha1(hash.encode())
        password = hash.hexdigest()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return redirect(url_for('home'))
        else:
            msg = 'Неверный логин/пароль.'
    return render_template('index.html', msg=msg)


@app.route('/musicwebplayer/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/musicwebplayer/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            msg = 'Аккаунт с такими данными уже существует.'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Email указан неверно.'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Имя должно содержать только буквы и цифры.'
        elif not username or not password or not email:
            msg = 'Вы пропустили поле.'
        else:
            hash = password + app.secret_key
            hash = hashlib.sha1(hash.encode())
            password = hash.hexdigest()
            cursor.execute('INSERT INTO accounts VALUES (NULL, %s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            msg = 'Вы успешно зарегистрировались!'
    elif request.method == 'POST':
        msg = 'Данные должны быть заполнены!'
    return render_template('register.html', msg=msg)


@app.route('/musicwebplayer/home')
def home():
    if 'loggedin' in session:
        return render_template('home.html', username=session['username'])
    else:
        return redirect(url_for('login'))


@app.route('/musicwebplayer/tracks')
def get_tracks():
    api_key = API_KEY
    api_url = "https://api.jamendo.com/v3.0"
    endpoint = "/tracks"
    params = {
        "client_id": api_key,
        "format": "json",
        "limit": 200
    }

    response = requests.get(api_url + endpoint, params=params)
    data = response.json()

    if "results" in data:
        tracks = random.sample(data["results"], 10)
        return render_template('tracks.html', tracks=tracks)
    else:
        return "Ошибка получения данных"


@app.route('/musicwebplayer/profile')
def profile():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM accounts WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        return render_template('profile.html', account=account)
    else:
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)