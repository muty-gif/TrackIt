"""Task endpoints addressed directly: /api/tasks/<id>."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from ..access import get_owned_task_or_404
from ..auth.utils import login_required
from ..extensions import db
from ..models import TaskStatus
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

    if "title" in data:
        task.title = validator.string(
            data, "title", max_length=current_app.config["TASK_TITLE_MAX_LENGTH"]
        )
    if "description" in data:
        task.description = validator.string(
            data, "description", required=False, max_length=current_app.config["TEXT_MAX_LENGTH"]
        )
    if "status" in data:
        task.status = validator.choice(data, "status", TaskStatus.ALL)

    validator.raise_if_errors()

    db.session.commit()
    return jsonify({"task": task.to_dict()})


@tasks_bp.delete("/<int:task_id>")
@login_required
def delete_task(task_id: int):
    task = get_owned_task_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return "", 204
