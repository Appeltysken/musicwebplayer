import unittest
from unittest.mock import patch
from app import app


class TestApp(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_home_page_logged_in(self):
        with self.app as client:
            with client.session_transaction() as sess:
                sess["loggedin"] = True
                sess["username"] = "testuser"
            response = client.get("/musicwebplayer/home")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"testuser", response.data)

    def test_home_page_not_logged_in(self):
        with self.app as client:
            response = client.get("/musicwebplayer/home")
            self.assertEqual(response.status_code, 302)
            self.assertIn(b"Redirecting", response.data)

    def test_get_tracks_logged_in(self):
        with self.app as client:
            with client.session_transaction() as sess:
                sess["loggedin"] = True
                sess["username"] = "testuser"
            response = client.get("/musicwebplayer/tracks")
            self.assertEqual(response.status_code, 200)

    def test_get_tracks_not_logged_in(self):
        with self.app as client:
            response = client.get("/musicwebplayer/tracks")
            self.assertEqual(response.status_code, 302)
            self.assertIn(b"Redirecting", response.data)

    def test_profile_not_logged_in(self):
        with self.app as client:
            response = client.get("/musicwebplayer/profile")
            self.assertEqual(response.status_code, 302)
            self.assertIn(b"Redirecting", response.data)


if __name__ == "__main__":
    unittest.main()