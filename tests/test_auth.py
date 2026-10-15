"""Authentication use cases: UC-A1 register, UC-A2 login, UC-A3 logout, UC-A4 me."""

from __future__ import annotations

from tests.base import BaseTestCase


class RegisterTests(BaseTestCase):
    def test_register_creates_account_and_logs_in(self):
        response = self.register("alice@example.com", "password123")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["user"]["email"], "alice@example.com")

        me = self.get("/api/auth/me")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.get_json()["user"]["email"], "alice@example.com")

    def test_email_is_normalised(self):
        response = self.register("  Alice@Example.COM ", "password123")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["user"]["email"], "alice@example.com")

    def test_duplicate_email_is_rejected(self):
        self.register("alice@example.com")
        response = self.register("alice@example.com")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["error"]["code"], "conflict")

    def test_duplicate_email_is_case_insensitive(self):
        self.register("alice@example.com")
        response = self.register("ALICE@example.com")
        self.assertEqual(response.status_code, 409)

    def test_invalid_email_is_rejected(self):
        response = self.register("not-an-email")
        self.assertEqual(response.status_code, 422)
        self.assertIn("email", response.get_json()["error"]["fields"])

    def test_short_password_is_rejected(self):
        response = self.register("alice@example.com", "short")
        self.assertEqual(response.status_code, 422)
        self.assertIn("password", response.get_json()["error"]["fields"])

    def test_missing_fields_are_reported(self):
        response = self.post("/api/auth/register", {})
        self.assertEqual(response.status_code, 422)
        fields = response.get_json()["error"]["fields"]
        self.assertIn("email", fields)
        self.assertIn("password", fields)

    def test_non_json_body_is_rejected(self):
        response = self.client.post(
            "/api/auth/register", data="not json", content_type="text/plain"
        )
        self.assertEqual(response.status_code, 415)


class LoginTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.register("alice@example.com", "password123")
        self.logout()

    def test_login_with_correct_credentials(self):
        response = self.login("alice@example.com", "password123")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.get("/api/auth/me").status_code, 200)

    def test_login_with_wrong_password(self):
        response = self.login("alice@example.com", "wrong-password")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"]["code"], "invalid_credentials")

    def test_login_with_unknown_email_uses_same_error(self):
        response = self.login("nobody@example.com", "password123")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"]["code"], "invalid_credentials")

    def test_me_requires_authentication(self):
        response = self.get("/api/auth/me")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"]["code"], "unauthorized")


class LogoutTests(BaseTestCase):
    def test_logout_clears_the_session(self):
        self.register("alice@example.com")
        self.assertEqual(self.get("/api/auth/me").status_code, 200)

        response = self.logout()
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.get("/api/auth/me").status_code, 401)

    def test_logout_without_a_session_is_a_no_op(self):
        response = self.logout()
        self.assertEqual(response.status_code, 204)
