from unittest.mock import MagicMock, patch
import unittest
import mysql.connector.errors as mysql_errors
from app import app


class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    @patch("app.mysql")
    def test_profile_route_loggedin(self, mock_mysql):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "username": "testuser",
        }
        mock_mysql.connection.cursor.return_value = mock_cursor
        with self.app as client:
            with client.session_transaction() as sess:
                sess["loggedin"] = True
                sess.pop("user_id", None)
                sess["id"] = 1
            response = client.get("/musicwebplayer/profile")
            self.assertEqual(response.status_code, 200)

    @patch("app.mysql")
    def test_profile_route_not_loggedin(self, mock_mysql):
        with self.app as client:
            response = client.get("/musicwebplayer/profile")
            self.assertEqual(response.status_code, 302)

    @patch("app.hashlib")
    @patch("app.mysql")
    def test_login_route_with_valid_credentials(self, mock_mysql, mock_hashlib):
        mock_hashlib.sha1.return_value.hexdigest.return_value = "hashed_password"
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "username": "testuser",
            "password": "hashed_password",
        }
        mock_mysql.connection.cursor.return_value = mock_cursor
        with self.app as client:
            response = client.post(
                "/musicwebplayer",
                data={"username": "testuser", "password": "password"},
                follow_redirects=True,
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"testuser", response.data)

    @patch("app.hashlib")
    @patch("app.mysql")
    def test_login_route_with_invalid_credentials(self, mock_mysql, mock_hashlib):
        mock_hashlib.sha1.return_value.hexdigest.return_value = "hashed_password"
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_mysql.connection.cursor.return_value = mock_cursor
        with self.app as client:
            response = client.post(
                "/musicwebplayer",
                data={"username": "testuser", "password": "password"},
                follow_redirects=True,
            )
            self.assertEqual(response.status_code, 200)

    @patch("app.mysql")
    def test_logout_route(self, mock_mysql):
        with self.app as client:
            with client.session_transaction() as sess:
                sess["loggedin"] = True
            response = client.get("/musicwebplayer/logout", follow_redirects=True)
            self.assertEqual(response.status_code, 200)

    @patch("app.mysql")
    def test_register_route_with_valid_credentials(self, mock_mysql):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_mysql.connection.cursor.return_value = mock_cursor
        with self.app as client:
            response = client.post(
                "/musicwebplayer/register",
                data={
                    "username": "testuser",
                    "password": "password",
                    "email": "testuser@example.com",
                },
                follow_redirects=True,
            )
            self.assertEqual(response.status_code, 200)

    @patch("app.mysql")
    def test_register_route_with_existing_account(self, mock_mysql):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "id": 1,
            "username": "testuser",
            "password": "hashed_password",
        }
        mock_mysql.connection.cursor.return_value = mock_cursor
        with self.app as client:
            response = client.post(
                "/musicwebplayer/register",
                data={
                    "username": "testuser",
                    "password": "password",
                    "email": "testuser@example.com",
                },
                follow_redirects=True,
            )
            self.assertEqual(response.status_code, 200)

    @patch("app.mysql")
    @patch("mysql.connector.errors.OperationalError")
    def test_register_route_with_invalid_email(self, mock_mysql_error, mock_mysql):
        mock_mysql_error.side_effect = mysql_errors.OperationalError("", "")
        with self.app as client:
            response = client.post(
                "/musicwebplayer/register",
                data={
                    "username": "testuser",
                    "password": "password",
                    "email": "invalid_email",
                },
                follow_redirects=True,
            )
            self.assertEqual(response.status_code, 200)

    @patch("app.mysql")
    @patch("mysql.connector.errors.OperationalError")
    def test_register_route_with_invalid_username(self, mock_mysql_error, mock_mysql):
        mock_mysql_error.side_effect = mysql_errors.OperationalError("", "")
        with self.app as client:
            response = client.post(
                "/musicwebplayer/register",
                data={
                    "username": "testuser@",
                    "password": "password",
                    "email": "testuser@example.com",
                },
                follow_redirects=True,
            )
            self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
