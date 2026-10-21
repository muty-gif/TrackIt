"""Task endpoints addressed directly: /api/tasks/<id>."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from ..access import get_owned_task_or_404
from ..auth.utils import login_required
from ..extensions import db
from ..models import TaskPriority, TaskStatus, utcnow
from ..validation import Validator, get_json_body

tasks_bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")


@tasks_bp.get("/<int:task_id>")
@login_required
def get_task(task_id: int):
    task = get_owned_task_or_404(task_id)
    return jsonify({"task": task.to_dict()})


@tasks_bp.patch("/<int:task_id>")
@login_required
def update_task(task_id: int):
    task = get_owned_task_or_404(task_id)
    data = get_json_body()

    validator = Validator()

    if "project_id" in data and data["project_id"] != task.project_id:
        # A task belongs to exactly one project and cannot be moved.
        validator.errors["project_id"] = "A task cannot be moved to another project."

    title = task.title
    description = task.description
    status = task.status
    priority = task.priority
    due_date = task.due_date

    if "title" in data:
        title = validator.string(
            data, "title", max_length=current_app.config["TASK_TITLE_MAX_LENGTH"]
        )
    if "description" in data:
        description = validator.string(
            data, "description", required=False, max_length=current_app.config["TEXT_MAX_LENGTH"]
        )
    if "status" in data:
        status = validator.choice(data, "status", TaskStatus.ALL)
    if "priority" in data:
        priority = validator.choice(data, "priority", TaskPriority.ALL)
    if "due_date" in data:
        due_date = validator.date(data)

    validator.raise_if_errors()

    task.title = title
    task.description = description
    task.priority = priority
    task.due_date = due_date
    if status == TaskStatus.COMPLETED:
        if task.completed_at is None:
            task.completed_at = utcnow()
    else:
        task.completed_at = None
    task.status = status

    db.session.commit()
    return jsonify({"task": task.to_dict()})


@tasks_bp.delete("/<int:task_id>")
@login_required
def delete_task(task_id: int):
    task = get_owned_task_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return "", 204
