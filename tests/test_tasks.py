"""Task use cases: UC-C1..UC-C6 plus nested ownership checks."""

from __future__ import annotations

from tests.base import BaseTestCase


class TaskCrudTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.register("alice@example.com")
        self.project_id = self.create_project("Website").get_json()["project"]["id"]

    def test_create_task_defaults_to_pending(self):
        response = self.create_task(self.project_id, "Write copy")
        self.assertEqual(response.status_code, 201)
        task = response.get_json()["task"]
        self.assertEqual(task["title"], "Write copy")
        self.assertEqual(task["status"], "pending")
        self.assertFalse(task["is_completed"])
        self.assertEqual(task["project_id"], self.project_id)
        self.assertEqual(task["priority"], "medium")
        self.assertIsNone(task["due_date"])
        self.assertIsNone(task["completed_at"])

    def test_create_task_with_priority_and_due_date(self):
        response = self.create_task(
            self.project_id, "Ship release", priority="high", due_date="2026-11-01"
        )
        self.assertEqual(response.status_code, 201)
        task = response.get_json()["task"]
        self.assertEqual(task["priority"], "high")
        self.assertEqual(task["due_date"], "2026-11-01")

    def test_invalid_priority_is_rejected(self):
        response = self.create_task(self.project_id, "One", priority="urgent")
        self.assertEqual(response.status_code, 422)
        self.assertIn("priority", response.get_json()["error"]["fields"])

    def test_invalid_due_date_is_rejected(self):
        response = self.create_task(self.project_id, "One", due_date="next week")
        self.assertEqual(response.status_code, 422)
        self.assertIn("due_date", response.get_json()["error"]["fields"])

    def test_in_progress_status_is_supported(self):
        task_id = self.create_task(self.project_id, "One").get_json()["task"]["id"]
        response = self.patch(f"/api/tasks/{task_id}", {"status": "in_progress"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["task"]["status"], "in_progress")
        self.assertFalse(response.get_json()["task"]["is_completed"])

    def test_completed_at_tracks_completion(self):
        task_id = self.create_task(self.project_id, "One").get_json()["task"]["id"]

        completed = self.patch(f"/api/tasks/{task_id}", {"status": "completed"}).get_json()["task"]
        self.assertIsNotNone(completed["completed_at"])

        reopened = self.patch(f"/api/tasks/{task_id}", {"status": "pending"}).get_json()["task"]
        self.assertIsNone(reopened["completed_at"])

    def test_create_task_requires_a_title(self):
        response = self.post(f"/api/projects/{self.project_id}/tasks", {"description": "x"})
        self.assertEqual(response.status_code, 422)
        self.assertIn("title", response.get_json()["error"]["fields"])

    def test_list_tasks(self):
        self.create_task(self.project_id, "One")
        self.create_task(self.project_id, "Two")
        response = self.get(f"/api/projects/{self.project_id}/tasks")
        self.assertEqual(response.status_code, 200)
        titles = [task["title"] for task in response.get_json()["tasks"]]
        self.assertEqual(titles, ["One", "Two"])

    def test_get_task_details(self):
        task_id = self.create_task(self.project_id, "One").get_json()["task"]["id"]
        response = self.get(f"/api/tasks/{task_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["task"]["id"], task_id)

    def test_update_task(self):
        task_id = self.create_task(self.project_id, "One").get_json()["task"]["id"]
        response = self.patch(f"/api/tasks/{task_id}", {"title": "One (revised)"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["task"]["title"], "One (revised)")

    def test_mark_task_completed_and_pending(self):
        task_id = self.create_task(self.project_id, "One").get_json()["task"]["id"]

        completed = self.patch(f"/api/tasks/{task_id}", {"status": "completed"})
        self.assertTrue(completed.get_json()["task"]["is_completed"])

        pending = self.patch(f"/api/tasks/{task_id}", {"status": "pending"})
        self.assertFalse(pending.get_json()["task"]["is_completed"])

    def test_marking_completed_twice_is_idempotent(self):
        task_id = self.create_task(self.project_id, "One").get_json()["task"]["id"]
        self.patch(f"/api/tasks/{task_id}", {"status": "completed"})
        response = self.patch(f"/api/tasks/{task_id}", {"status": "completed"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["task"]["is_completed"])

    def test_invalid_status_is_rejected(self):
        task_id = self.create_task(self.project_id, "One").get_json()["task"]["id"]
        response = self.patch(f"/api/tasks/{task_id}", {"status": "archived"})
        self.assertEqual(response.status_code, 422)
        self.assertIn("status", response.get_json()["error"]["fields"])

    def test_task_cannot_be_moved_to_another_project(self):
        other_project = self.create_project("Other").get_json()["project"]["id"]
        task_id = self.create_task(self.project_id, "One").get_json()["task"]["id"]
        response = self.patch(f"/api/tasks/{task_id}", {"project_id": other_project})
        self.assertEqual(response.status_code, 422)
        self.assertIn("project_id", response.get_json()["error"]["fields"])

    def test_delete_task(self):
        task_id = self.create_task(self.project_id, "One").get_json()["task"]["id"]
        self.assertEqual(self.delete(f"/api/tasks/{task_id}").status_code, 204)
        self.assertEqual(self.get(f"/api/tasks/{task_id}").status_code, 404)

    def test_update_and_delete_missing_task(self):
        self.assertEqual(self.patch("/api/tasks/999999", {"title": "x"}).status_code, 404)
        self.assertEqual(self.delete("/api/tasks/999999").status_code, 404)

    def test_nonexistent_parent_project(self):
        self.assertEqual(self.get("/api/projects/999999/tasks").status_code, 404)
        self.assertEqual(
            self.post("/api/projects/999999/tasks", {"title": "x"}).status_code, 404
        )


class TaskIsolationTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.make_user("alice@example.com")
        self.login("alice@example.com")
        self.alice_project_id = self.create_project("Alice project").get_json()["project"]["id"]
        self.alice_task_id = self.create_task(self.alice_project_id, "Alice task").get_json()["task"]["id"]
        self.logout()

        self.make_user("bob@example.com")
        self.login("bob@example.com")
        self.bob_project_id = self.create_project("Bob project").get_json()["project"]["id"]

    def test_cannot_list_tasks_of_other_users_project(self):
        self.assertEqual(self.get(f"/api/projects/{self.alice_project_id}/tasks").status_code, 404)

    def test_cannot_create_task_in_other_users_project(self):
        response = self.post(f"/api/projects/{self.alice_project_id}/tasks", {"title": "intruder"})
        self.assertEqual(response.status_code, 404)

    def test_cannot_read_other_users_task(self):
        self.assertEqual(self.get(f"/api/tasks/{self.alice_task_id}").status_code, 404)

    def test_cannot_update_other_users_task(self):
        response = self.patch(f"/api/tasks/{self.alice_task_id}", {"title": "hacked"})
        self.assertEqual(response.status_code, 404)

    def test_cannot_delete_other_users_task(self):
        self.assertEqual(self.delete(f"/api/tasks/{self.alice_task_id}").status_code, 404)
