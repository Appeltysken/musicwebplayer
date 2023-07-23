from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import hashlib
import os
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY")  # Секретный ключ (любой)
app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST")  # local host
app.config["MYSQL_USER"] = os.getenv("MYSQL_USER")  # root
app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD")
app.config["MYSQL_DB"] = os.getenv("MYSQL_DB")  # Название базы данных MySQL
app.config["TEMPLATES_AUTO_RELOAD"] = True
VKID = os.getenv("VKID")  # ID приложения

REDIRECTURI = "http://127.0.0.1:5000/login_vk"  # Редирект посетителя после авторизации
VKSECRET = os.getenv("VK_SECRET")

app.jinja_env.globals.update(VKID=VKID)  # ID приложения
app.jinja_env.globals.update(REDIRECTURI=REDIRECTURI)  # Редирект

mysql = MySQL(app)

class Database:
    def create_database():
        db_connection = MySQLdb.connect(
            host=os.getenv("MYSQL_HOST"),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
        )
        db_cursor = db_connection.cursor()
        db_cursor.execute("CREATE DATABASE IF NOT EXISTS songshackdb")
        db_cursor.execute(
            "CREATE TABLE IF NOT EXISTS songshackdb.accounts ("
            "id INT AUTO_INCREMENT PRIMARY KEY,"
            "username VARCHAR(255) NOT NULL,"
            "password VARCHAR(255) NOT NULL,"
            "email VARCHAR(255) NOT NULL"
            ")"
        )
        db_cursor.execute(
            "CREATE TABLE IF NOT EXISTS songshackdb.users ("
            "user_id INT PRIMARY KEY,"
            "username VARCHAR(255) NOT NULL"
            ")"
        )
        db_connection.close()

Database.create_database()

class User:
    def __init__(self, username, password, email):
        self.username = username
        self.password = password
        self.email = email

    def save_to_database(self):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        hashed_password = hashlib.sha1((self.password + app.secret_key).encode()).hexdigest()
        cursor.execute(
            "INSERT INTO accounts (username, password, email) VALUES (%s, %s, %s)",
            (self.username, hashed_password, self.email),
        )
        mysql.connection.commit()


class User_VK:
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username

    @staticmethod
    def get_user_by_username_password(username, password):
        hashed_password = hashlib.sha1((password + app.secret_key).encode()).hexdigest()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "SELECT * FROM accounts WHERE username = %s AND password = %s",
            (username, hashed_password),
        )
        return cursor.fetchone()

    @staticmethod
    def get_user_by_user_id(user_id):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        return cursor.fetchone()

    def save_to_database(self):
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "INSERT INTO users (user_id, username) VALUES (%s, %s)",
            (self.user_id, self.username),
        )
        mysql.connection.commit()


class WebPlayerApp:
    def __init__(self, app):
        self.app = app

    def run(self):
        self.app.run(debug=True)

    def render_template(self, tmpl_name, **kwargs):
        vk = False
        user_id = session.get("user_id")
        first_name = session.get("first_name")

        if user_id:
            vk = True
        return render_template(tmpl_name, vk=vk, user_id=user_id, name=first_name, **kwargs)

    def index(self):
        return self.render_template("index.html")

    def login_vk(self):
        code = request.args.get("code")

        response = requests.get(
            f"https://oauth.vk.com/access_token?client_id={VKID}&redirect_uri={REDIRECTURI}&client_secret={VKSECRET}&code={code}"
        )

        access_token = response.json().get("access_token")
        if not access_token:
            return "Failed to retrieve access token"
        params = {
            "v": "5.101",
            "fields": "uid,first_name,last_name",
            "access_token": access_token,
        }

        get_info = requests.get(f"https://api.vk.com/method/users.get", params=params)
        get_info = get_info.json().get("response")
        if not get_info:
            return "Failed to retrieve user info"
        get_info = get_info[0]

        session_data = {
            "loggedin": True,
            "user_id": get_info.get("id"),
            "first_name": get_info.get("first_name"),
            "last_name": get_info.get("last_name"),
        }

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        username = session_data["first_name"] + " " + session_data["last_name"]
        user_id = session_data["user_id"]

        def check_user_id(user_id):
            try:
                query = "SELECT * FROM users WHERE user_id = %s"
                cursor.execute(query, (user_id,))
                result = cursor.fetchone()
                return bool(result)
            except mysql.connection.Error as error:
                print("Error:", error)
                return False

        if check_user_id(user_id):
            session_data["username"] = username
        else:
            cursor.execute(
                "INSERT INTO users (user_id, username) VALUES (%s, %s)",
                (
                    user_id,
                    username,
                ),
            )
            mysql.connection.commit()
        session.update(session_data)
        return redirect(url_for("home"))


# Routes
@app.route("/", methods=["GET", "POST"])
@app.route("/musicwebplayer", methods=["GET", "POST"])
def login():
    msg = ""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username and password:
            hash = hashlib.sha1((password + app.secret_key).encode()).hexdigest()
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                "SELECT * FROM accounts WHERE username = %s AND password = %s",
                (username, hash),
            )
            account = cursor.fetchone()
            if account:
                session_data = {
                    "loggedin": True,
                    "id": account["id"],
                    "username": account["username"],
                }
                session.update(session_data)
                return redirect(url_for("home"))
            else:
                msg = "Неверный логин/пароль."
    return render_template("index.html", msg=msg)


@app.route("/musicwebplayer/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/musicwebplayer/register", methods=["GET", "POST"])
def register():
    msg = ""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        if username and password and email:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute("SELECT * FROM accounts WHERE username = %s", (username,))
            account = cursor.fetchone()
            if account:
                msg = "Аккаунт с такими данными уже существует."
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                msg = "Email указан неверно."
            elif not re.match(r"[A-Za-z0-9]+", username):
                msg = "Имя должно содержать только буквы и цифры."
            else:
                hashed_password = hashlib.sha1(
                    (password + app.secret_key).encode()
                ).hexdigest()
                cursor.execute(
                    "INSERT INTO accounts (username, password, email) VALUES (%s, %s, %s)",
                    (username, hashed_password, email),
                )
                mysql.connection.commit()
                msg = "Вы успешно зарегистрировались!"
        else:
            msg = "Вы пропустили поле."
    return render_template("register.html", msg=msg)

@app.route("/musicwebplayer/home")
def home():
    if "loggedin" in session:
        return render_template("home.html", username=session.get("username"))
    return redirect(url_for("login"))


@app.route("/musicwebplayer/tracks")
def get_tracks():
    if "loggedin" in session:
        return render_template("tracks.html", username=session["username"])
    else:
        return redirect(url_for("login"))


@app.route("/musicwebplayer/profile")
def profile():
    if "loggedin" in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        if "user_id" in session:

            cursor.execute("SELECT * FROM users WHERE user_id = %s", (session["user_id"],))
            user_data = cursor.fetchone()

            if user_data:
                return render_template("profile.html", account=user_data)
        else:
            cursor.execute("SELECT * FROM accounts WHERE id = %s", (session["id"],))
            account = cursor.fetchone()

            if account:
                return render_template("profile.html", account=account)

    return redirect(url_for("login"))


if __name__ == "__main__":
    web_player_app = WebPlayerApp(app)
    web_player_app.run()