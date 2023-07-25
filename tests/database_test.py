import unittest
from unittest.mock import patch, MagicMock
from app import app, mysql
from dotenv import load_dotenv
import os

load_dotenv()

class TestApp(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["MYSQL_DB"] = os.getenv("MYSQL_DB")
        app.config["MYSQL_USER"] = os.getenv("MYSQL_USER")
        app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD")
        app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST")
        self.app = app.test_client()
        with app.app_context():
            with mysql.connection.cursor() as cursor:
                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS songshackdb.accounts ("
                    "id INT AUTO_INCREMENT PRIMARY KEY,"
                    "username VARCHAR(255) NOT NULL,"
                    "password VARCHAR(255) NOT NULL,"
                    "email VARCHAR(255) NOT NULL"
                    ")"
                )

    def test_login_success(self):
        with app.app_context():
            with mysql.connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO songshackdb.accounts (username, password, email) VALUES (%s, %s, %s)",
                    ("testuser", "testpassword", "testemail"),
                )
                mysql.connection.commit()

        response = self.app.post(
            "/musicwebplayer",
            data={"username": "testuser", "password": "testpassword"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_login_failure(self):
        response = self.app.post(
            "/musicwebplayer",
            data={"username": "testuser", "password": "testpassword"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

    @patch("requests.get")
    def test_get_tracks_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": [{"name": "testtrack"}]}
        mock_get.return_value = mock_response

        with app.app_context():
            with self.app.session_transaction() as session:
                session["loggedin"] = True
                session["username"] = "testuser"

        response = self.app.get("/musicwebplayer/tracks")
        self.assertEqual(response.status_code, 200)

    def test_get_tracks_failure(self):
        response = self.app.get("/musicwebplayer/tracks")
        self.assertEqual(response.status_code, 302)


if __name__ == "__main__":
    unittest.main()