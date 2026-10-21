"""Dashboard API: user-scoped metrics, status breakdown and quick lists."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from tests.base import BaseTestCase


def _today():
    return datetime.now(timezone.utc).date()


class DashboardTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.register("alice@example.com")
        self.project_id = self.create_project("Website").get_json()["project"]["id"]

    def test_dashboard_requires_authentication(self):
        self.logout()
        self.assertEqual(self.get("/api/dashboard").status_code, 401)

    def test_empty_dashboard(self):
        response = self.get("/api/dashboard")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(
            data["metrics"],
            {
                "project_count": 1,
                "open_task_count": 0,
                "completed_this_week": 0,
                "overdue_task_count": 0,
                "due_today_count": 0,
            },
        )
        self.assertEqual(
            data["status_counts"], {"pending": 0, "in_progress": 0, "completed": 0}
        )
        self.assertEqual(data["upcoming"], [])
        self.assertEqual(len(data["recent"]), 1)

    def test_metrics_status_counts_and_lists(self):
        today = _today()
        yesterday = (today - timedelta(days=1)).isoformat()
        tomorrow = (today + timedelta(days=1)).isoformat()

        self.create_task(self.project_id, "Overdue", due_date=yesterday)
        self.create_task(
            self.project_id,
            "In progress today",
            status="in_progress",
            priority="high",
            due_date=today.isoformat(),
        )
        self.create_task(self.project_id, "Upcoming", due_date=tomorrow)
        self.create_task(self.project_id, "Finished", status="completed")
        self.create_task(self.project_id, "Someday")

        data = self.get("/api/dashboard").get_json()

        self.assertEqual(data["metrics"]["project_count"], 1)
        self.assertEqual(data["metrics"]["open_task_count"], 4)
        self.assertEqual(data["metrics"]["completed_this_week"], 1)
        self.assertEqual(data["metrics"]["overdue_task_count"], 1)
        self.assertEqual(data["metrics"]["due_today_count"], 1)
        self.assertEqual(
            data["status_counts"], {"pending": 3, "in_progress": 1, "completed": 1}
        )

        self.assertEqual(
            [task["title"] for task in data["upcoming"]],
            ["In progress today", "Upcoming"],
        )
        self.assertEqual(data["upcoming"][0]["project_name"], "Website")
        self.assertEqual(data["projects"][0]["task_count"], 5)
        self.assertEqual(data["projects"][0]["completed_task_count"], 1)
        self.assertTrue(any(item["kind"] == "task" for item in data["recent"]))

    def test_dashboard_is_scoped_to_the_current_user(self):
        self.create_task(self.project_id, "Alice task", due_date=_today().isoformat())
        self.logout()

        self.make_user("bob@example.com")
        self.login("bob@example.com")

        data = self.get("/api/dashboard").get_json()
        self.assertEqual(data["metrics"]["project_count"], 0)
        self.assertEqual(data["metrics"]["open_task_count"], 0)
        self.assertEqual(data["projects"], [])
        self.assertEqual(data["upcoming"], [])
        self.assertEqual(data["recent"], [])
