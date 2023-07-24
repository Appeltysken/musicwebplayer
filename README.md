# Music Web Player
### 📦 Зависимости:
1. [Python 3.11.4.](https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe)
2. [MySQL сервер.](https://dev.mysql.com/downloads/file/?id=520406)

### 🚀 Установка:
1. Установить необходимые библиотеки:
```
pip install -r requirements.txt
```
2. Создать и настроить .env файл:
```
APP_SECRET_KEY=YOUR_APP_SECRET_KEY
MYSQL_HOST=YOUR_MYSQL_HOST
MYSQL_USER=YOUR_MYSQL_USER
MYSQL_PASSWORD=YOUR_MYSQL_PASSWORD
MYSQL_DB=songshackdb
VKID=YOUR_VKID
VK_SECRET=YOUR_VK_SECRET
```
3. Начать использовать:
```
python app.py
```