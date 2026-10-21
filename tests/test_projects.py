"""Project use cases: UC-B1..UC-B5 plus ownership isolation (UC-D1..UC-D3)."""

from __future__ import annotations

from trackit.extensions import db
from trackit.models import Task
from tests.base import BaseTestCase


class ProjectCrudTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.register("alice@example.com")
        self.user_id = self.get("/api/auth/me").get_json()["user"]["id"]

    def test_list_requires_authentication(self):
        self.logout()
        response = self.get("/api/projects")
        self.assertEqual(response.status_code, 401)

    def test_create_project(self):
        response = self.create_project("Website", "Build the marketing site")
        self.assertEqual(response.status_code, 201)
        project = response.get_json()["project"]
        self.assertEqual(project["name"], "Website")
        self.assertEqual(project["description"], "Build the marketing site")
        self.assertEqual(project["tasks"], [])
        self.assertIsNone(project["due_date"])

    def test_create_and_update_project_due_date(self):
        response = self.post(
            "/api/projects", {"name": "Website", "due_date": "2026-12-01"}
        )
        self.assertEqual(response.status_code, 201)
        project = response.get_json()["project"]
        self.assertEqual(project["due_date"], "2026-12-01")

        updated = self.patch(
            f"/api/projects/{project['id']}", {"due_date": "2026-12-15"}
        )
        self.assertEqual(updated.get_json()["project"]["due_date"], "2026-12-15")

        cleared = self.patch(f"/api/projects/{project['id']}", {"due_date": None})
        self.assertIsNone(cleared.get_json()["project"]["due_date"])

    def test_invalid_project_due_date_is_rejected(self):
        response = self.post(
            "/api/projects", {"name": "Website", "due_date": "soon"}
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("due_date", response.get_json()["error"]["fields"])

    def test_create_project_requires_a_name(self):
        response = self.post("/api/projects", {"description": "no name"})
        self.assertEqual(response.status_code, 422)
        self.assertIn("name", response.get_json()["error"]["fields"])

    def test_list_returns_counters(self):
        project_id = self.create_project("Website").get_json()["project"]["id"]
        self.create_task(project_id, "Task A")
        task_b = self.create_task(project_id, "Task B").get_json()["task"]["id"]
        self.patch(f"/api/tasks/{task_b}", {"status": "completed"})

        response = self.get("/api/projects")
        self.assertEqual(response.status_code, 200)
        projects = response.get_json()["projects"]
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["task_count"], 2)
        self.assertEqual(projects[0]["completed_task_count"], 1)

    def test_get_project_details_includes_tasks(self):
        project_id = self.create_project("Website").get_json()["project"]["id"]
        self.create_task(project_id, "Task A")

        response = self.get(f"/api/projects/{project_id}")
        self.assertEqual(response.status_code, 200)
        project = response.get_json()["project"]
        self.assertEqual(len(project["tasks"]), 1)
        self.assertEqual(project["tasks"][0]["title"], "Task A")

    def test_update_project(self):
        project_id = self.create_project("Old name").get_json()["project"]["id"]
        response = self.patch(f"/api/projects/{project_id}", {"name": "New name"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["project"]["name"], "New name")

    def test_update_project_with_invalid_data(self):
        project_id = self.create_project("Website").get_json()["project"]["id"]
        response = self.patch(f"/api/projects/{project_id}", {"name": "   "})
        self.assertEqual(response.status_code, 422)

    def test_delete_project(self):
        project_id = self.create_project("Website").get_json()["project"]["id"]
        response = self.delete(f"/api/projects/{project_id}")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.get(f"/api/projects/{project_id}").status_code, 404)

    def test_deleting_a_project_cascades_to_tasks(self):
        project_id = self.create_project("Website").get_json()["project"]["id"]
        task_id = self.create_task(project_id, "Task A").get_json()["task"]["id"]

        self.delete(f"/api/projects/{project_id}")

        self.assertEqual(db.session.get(Task, task_id), None)
        self.assertEqual(db.session.query(Task).count(), 0)


class ProjectIsolationTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.make_user("alice@example.com")
        self.login("alice@example.com")
        self.alice_project_id = self.create_project("Alice project").get_json()["project"]["id"]
        self.logout()

        self.make_user("bob@example.com")
        self.login("bob@example.com")

    def test_list_only_returns_own_projects(self):
        response = self.get("/api/projects")
        self.assertEqual(response.get_json()["projects"], [])

    def test_other_users_project_is_not_found(self):
        self.assertEqual(self.get(f"/api/projects/{self.alice_project_id}").status_code, 404)

    def test_cannot_update_other_users_project(self):
        response = self.patch(f"/api/projects/{self.alice_project_id}", {"name": "hacked"})
        self.assertEqual(response.status_code, 404)

    def test_cannot_delete_other_users_project(self):
        self.assertEqual(self.delete(f"/api/projects/{self.alice_project_id}").status_code, 404)

    def test_nonexistent_project_is_not_found(self):
        self.assertEqual(self.get("/api/projects/999999").status_code, 404)
        self.assertEqual(self.patch("/api/projects/999999", {"name": "x"}).status_code, 404)
        self.assertEqual(self.delete("/api/projects/999999").status_code, 404)
