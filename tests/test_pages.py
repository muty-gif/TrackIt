"""Page-level behavior (UC-D1) and JSON error shape for the API."""

from __future__ import annotations

from tests.base import BaseTestCase


class PageGuardTests(BaseTestCase):
    def test_root_redirects_anonymous_visitor_to_login(self):
        response = self.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_login_page_is_public(self):
        self.assertEqual(self.get("/login").status_code, 200)
        self.assertEqual(self.get("/register").status_code, 200)

    def test_protected_page_redirects_anonymous_visitor(self):
        response = self.get("/projects")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    def test_protected_page_visible_when_authenticated(self):
        self.register("alice@example.com")
        response = self.get("/projects")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Your projects", response.get_data(as_text=True))

    def test_login_page_redirects_authenticated_user(self):
        self.register("alice@example.com")
        response = self.get("/login")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/projects", response.headers["Location"])


class ApiErrorShapeTests(BaseTestCase):
    def test_unknown_api_route_returns_json_404(self):
        response = self.get("/api/does-not-exist")
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())

    def test_method_not_allowed_returns_json(self):
        response = self.client.put("/api/projects")
        self.assertEqual(response.status_code, 405)
        self.assertIn("error", response.get_json())
