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
        """
        Создает базу данных и таблицы, если их не существует.
        Таблицы: accounts, users.
        accounts - хранит информацию о зарегистрированных пользователях обычным способ.
        users - хранит информацию о пользователях, которые авторизовались через VK.
        """
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


@app.route("/")
@app.route("/musicwebplayer", methods=["GET", "POST"])
def login():
    """
    Функция для обработки GET и POST запросов на главную страницу приложения.
    Если метод запроса POST, то функция проверяет введенные данные пользователя и, если они верны,
    создает сессию и перенаправляет пользователя на страницу home.
    Если метод запроса GET, то функция возвращает шаблон страницы index.html.
    """
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
                user = account
                return redirect(url_for("home"))
            else:
                msg = "Неверный логин/пароль."
    return render_template("index.html", msg=msg)


@app.route("/musicwebplayer/logout")
def logout():
    """
    Функция для выхода пользователя из системы.
    Она очищает сессию и перенаправляет пользователя на страницу авторизации.
    """
    session.clear()
    return redirect(url_for("login"))


@app.route("/musicwebplayer/register", methods=["GET", "POST"])
def register():
    """
    Функция для обработки GET и POST запросов на страницу регистрации.
    Если метод запроса POST, то функция проверяет введенные данные пользователя и, если они верны,
    создает новый аккаунт в базе данных и перенаправляет пользователя на страницу авторизации.
    Если метод запроса GET, то функция возвращает шаблон страницы register.html.
    """
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
    """
    Функция для обработки GET запросов на домашнюю страницу.
    Если пользователь авторизован, то функция возвращает шаблон страницы home.html с именем пользователя.
    Если пользователь не авторизован, то функция перенаправляет пользователя на страницу авторизации.
    """
    if "loggedin" in session:
        return render_template("home.html", username=session.get("username"))
    return redirect(url_for("login"))


@app.route("/musicwebplayer/tracks")
def get_tracks():
    """
    Функция для обработки GET запросов на страницу со списком треков.
    Если пользователь авторизован, то функция возвращает шаблон страницы tracks.html с именем пользователя.
    Если пользователь не авторизован, то функция перенаправляет пользователя на страницу авторизации.
    """
    if "loggedin" in session:
        return render_template("tracks.html", username=session["username"])
    else:
        return redirect(url_for("login"))


@app.route("/musicwebplayer/profile")
def profile():
    """
    Функция для обработки GET запросов на страницу профиля пользователя.
    Если пользователь авторизован, то функция возвращает шаблон страницы profile.html с данными пользователя.
    Если пользователь не авторизован, то функция перенаправляет пользователя на страницу авторизации.
    """
    if "loggedin" in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        if "user_id" in session:
            cursor.execute(
                "SELECT * FROM users WHERE user_id = %s", (session["user_id"],)
            )
            user_data = cursor.fetchone()

            if user_data:
                return render_template("profile.html", account=user_data)
        else:
            cursor.execute("SELECT * FROM accounts WHERE id = %s", (session["id"],))
            account = cursor.fetchone()

            if account:
                return render_template("profile.html", account=account)
    return redirect(url_for("login"))


@app.before_request
def make_session_permanent():
    """
    Функция, которая устанавливает сессию как постоянную при каждом запросе.
    """
    session.permanent = True


def template(tmpl_name, **kwargs):
    """
    Функция для рендеринга шаблона с передачей параметров.
    :param tmpl_name: Имя шаблона.
    :param kwargs: Передаваемые параметры.
    :return: Рендеринг шаблона с передачей параметров.
    """
    vk = False
    user_id = session.get("user_id")
    first_name = session.get("first_name")

    if user_id:
        vk = True
    return render_template(tmpl_name, vk=vk, user_id=user_id, name=first_name, **kwargs)


@app.route("/login_vk")
def login_vk():
    """
    Функция для обработки GET запросов на страницу авторизации через ВКонтакте.
    Если пользователь авторизован, то функция перенаправляет пользователя на страницу home.
    Если пользователь не авторизован, то функция перенаправляет пользователя на страницу авторизации ВКонтакте.
    """
    code = request.args.get("code")

    response = requests.get(
        f"https://oauth.vk.com/access_token?client_id={VKID}&redirect_uri={REDIRECTURI}&client_secret={VKSECRET}&code={code}"
    )

    params = {
        "v": "5.101",
        "fields": "uid,first_name,last_name,screen_name,sex,bdate,photo_big",
        "access_token": response.json()["access_token"],
    }

    get_info = requests.get(f"https://api.vk.com/method/users.get", params=params)
    get_info = get_info.json()["response"][0]

    session["loggedin"] = True
    session["user_id"] = get_info["id"]
    session["first_name"] = get_info["first_name"]
    session["last_name"] = get_info["last_name"]

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    username = session["first_name"] + " " + session["last_name"]
    user_id = session["user_id"]

    def check_user_id(user_id):
        """
        Функция для проверки наличия пользователя в базе данных.
        :param user_id: ID пользователя.
        :return: True, если пользователь существует в базе данных, иначе False.
        """
        try:
            query = "SELECT * FROM users WHERE user_id = %s"
            cursor.execute(query, (user_id,))

            result = cursor.fetchone()

            if result:
                user_exists = True
            else:
                user_exists = False
            print(user_exists)
            return user_exists
        except mysql.connection.Error as error:
            print("Error:", error)
            return False

    if check_user_id(user_id):
        session["username"] = username
        return redirect(url_for("home"))
    else:
        cursor.execute(
            "INSERT INTO users (user_id, username) VALUES (%s, %s)",
            (
                user_id,
                username,
            ),
        )
        mysql.connection.commit()
    session["username"] = username
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
