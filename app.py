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

app.secret_key = os.getenv("APP_SECRET_KEY")  # your secret key
app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST")  # local host
app.config["MYSQL_USER"] = os.getenv("MYSQL_USER")  # root
app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD")
app.config["MYSQL_DB"] = os.getenv("MYSQL_DB")  # name of db
app.config["TEMPLATES_AUTO_RELOAD"] = True
VKID = os.getenv(
    "VKID"
)  # ID приложения на vk.com/editapp?id=АйдиПриложения&section=options

REDIRECTURI = "http://127.0.0.1:5000/login_vk"  # Редирект посетителя после авторизации
VKSECRET = os.getenv("VK_SECRET")
API_KEY = os.getenv("API_KEY")  # API Jamendo

app.jinja_env.globals.update(VKID=VKID)  # айди приложения
app.jinja_env.globals.update(REDIRECTURI=REDIRECTURI)  # редирект

mysql = MySQL(app)


@app.route("/")
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
                session["loggedin"] = True
                session["id"] = account["id"]
                session["username"] = account["username"]
                return redirect(url_for("home"))
            else:
                msg = "Неверный логин/пароль."
    return render_template("index.html", msg=msg)


@app.route("/musicwebplayer/logout")
def logout():
    session.pop("loggedin", None)
    session.pop("id", None)
    session.pop("username", None)
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
                    "INSERT INTO accounts (username, password, email, favorite_tags) VALUES (%s, %s, %s, %s)",
                    (username, hashed_password, email, None),
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

        cursor.execute("SELECT * FROM users WHERE user_id = %s", (session["user_id"],))
        user_data = cursor.fetchone()

        if user_data:
            return render_template("profile.html", account=user_data)
        else:
            cursor.execute("SELECT * FROM accounts WHERE id = %s", (session["id"],))
            account = cursor.fetchone()
            return render_template("profile.html", account=account)
    else:
        return redirect(url_for("login"))


# VK AUTH


@app.before_request
def make_session_permanent():
    session.permanent = True


def template(tmpl_name, **kwargs):
    vk = False
    user_id = session.get("user_id")
    first_name = session.get("first_name")

    if user_id:
        vk = True
    return render_template(tmpl_name, vk=vk, user_id=user_id, name=first_name, **kwargs)


@app.route("/")
def index():
    return template("index.html")


@app.route("/logout_vk")
def logout_vk():
    session.pop("user_id")
    session.pop("username")

    return redirect(url_for("index"))


@app.route("/login_vk")
def login_vk():
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


if __name__ == "__main__":
    app.run(debug=True)
