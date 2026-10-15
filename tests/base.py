"""Shared test plumbing: an app bound to an in-memory SQLite database."""

from __future__ import annotations

import unittest

from trackit import create_app
from trackit.extensions import db


class BaseTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(
            overrides={
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
                "PASSWORD_MIN_LENGTH": 8,
            }
        )
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.ctx.pop()

    # --- request helpers --------------------------------------------------
    def post(self, url: str, payload: dict | None = None, **kwargs):
        return self.client.post(url, json=payload, **kwargs)

    def patch(self, url: str, payload: dict | None = None, **kwargs):
        return self.client.patch(url, json=payload, **kwargs)

    def get(self, url: str, **kwargs):
        return self.client.get(url, **kwargs)

    def delete(self, url: str, **kwargs):
        return self.client.delete(url, **kwargs)

    # --- domain helpers ---------------------------------------------------
    def register(self, email: str = "user@example.com", password: str = "password123"):
        return self.post("/api/auth/register", {"email": email, "password": password})

    def login(self, email: str = "user@example.com", password: str = "password123"):
        return self.post("/api/auth/login", {"email": email, "password": password})

    def logout(self):
        return self.post("/api/auth/logout")

    def create_project(self, name: str = "My project", description: str | None = None):
        return self.post("/api/projects", {"name": name, "description": description})

    def create_task(self, project_id: int, title: str = "My task", **extra):
        payload = {"title": title}
        payload.update(extra)
        return self.post(f"/api/projects/{project_id}/tasks", payload)

    def make_user(self, email: str, password: str = "password123") -> int:
        """Register a user and return their id, then log them out."""
        response = self.register(email=email, password=password)
        assert response.status_code == 201, response.get_data(as_text=True)
        user_id = response.get_json()["user"]["id"]
        self.logout()
        return user_id
