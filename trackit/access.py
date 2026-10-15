"""Ownership lookups.

A resource that does not exist and a resource owned by somebody else are both
reported as "not found" so the existence of another user's data is never leaked
(see USE-CASES.md UC-D2 / UC-D3).
"""

from __future__ import annotations

from flask import g

from .errors import NotFoundError
from .extensions import db
from .models import Project, Task


def get_owned_project_or_404(project_id: int) -> Project:
    current = getattr(g, "current_user", None)
    project = db.session.get(Project, project_id)
    if project is None or current is None or project.owner_id != current.id:
        raise NotFoundError("Project not found.")
    return project


def get_owned_task_or_404(task_id: int) -> Task:
    current = getattr(g, "current_user", None)
    task = db.session.get(Task, task_id)
    if task is None or current is None or task.project.owner_id != current.id:
        raise NotFoundError("Task not found.")
    return task
