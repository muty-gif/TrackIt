"""Project endpoints: /api/projects and the project's tasks."""

from __future__ import annotations

from flask import Blueprint, current_app, g, jsonify
from sqlalchemy import case, func

from ..access import get_owned_project_or_404
from ..auth.utils import login_required
from ..extensions import db
from ..models import Project, Task, TaskStatus
from ..validation import Validator, get_json_body

projects_bp = Blueprint("projects", __name__, url_prefix="/api/projects")


@projects_bp.get("")
@login_required
def list_projects():
    """List the current user's projects with task counters."""
    completed = func.coalesce(
        func.sum(case((Task.status == TaskStatus.COMPLETED, 1), else_=0)), 0
    )
    rows = db.session.execute(
        db.select(Project, func.count(Task.id), completed)
        .outerjoin(Task, Task.project_id == Project.id)
        .where(Project.owner_id == g.current_user.id)
        .group_by(Project.id)
        .order_by(Project.created_at.desc(), Project.id.desc())
    ).all()

    projects = [
        project.to_dict(task_count=task_count, completed_task_count=completed_count)
        for project, task_count, completed_count in rows
    ]
    return jsonify({"projects": projects})


@projects_bp.post("")
@login_required
def create_project():
    data = get_json_body()

    validator = Validator()
    name = validator.string(
        data, "name", max_length=current_app.config["PROJECT_NAME_MAX_LENGTH"]
    )
    description = validator.string(
        data, "description", required=False, max_length=current_app.config["TEXT_MAX_LENGTH"]
    )
    validator.raise_if_errors()

    project = Project(name=name, description=description, owner=g.current_user)
    db.session.add(project)
    db.session.commit()

    return jsonify({"project": project.to_dict(include_tasks=True)}), 201


@projects_bp.get("/<int:project_id>")
@login_required
def get_project(project_id: int):
    project = get_owned_project_or_404(project_id)
    return jsonify({"project": project.to_dict(include_tasks=True)})


@projects_bp.patch("/<int:project_id>")
@login_required
def update_project(project_id: int):
    project = get_owned_project_or_404(project_id)
    data = get_json_body()

    validator = Validator()
    if "name" in data:
        project.name = validator.string(
            data, "name", max_length=current_app.config["PROJECT_NAME_MAX_LENGTH"]
        )
    if "description" in data:
        project.description = validator.string(
            data, "description", required=False, max_length=current_app.config["TEXT_MAX_LENGTH"]
        )
    validator.raise_if_errors()

    db.session.commit()
    return jsonify({"project": project.to_dict(include_tasks=True)})


@projects_bp.delete("/<int:project_id>")
@login_required
def delete_project(project_id: int):
    project = get_owned_project_or_404(project_id)
    db.session.delete(project)  # tasks cascade
    db.session.commit()
    return "", 204


@projects_bp.get("/<int:project_id>/tasks")
@login_required
def list_tasks(project_id: int):
    project = get_owned_project_or_404(project_id)
    tasks = db.session.execute(
        db.select(Task)
        .where(Task.project_id == project.id)
        .order_by(Task.created_at.asc(), Task.id.asc())
    ).scalars().all()
    return jsonify({"tasks": [task.to_dict() for task in tasks]})


@projects_bp.post("/<int:project_id>/tasks")
@login_required
def create_task(project_id: int):
    project = get_owned_project_or_404(project_id)
    data = get_json_body()

    validator = Validator()
    title = validator.string(
        data, "title", max_length=current_app.config["TASK_TITLE_MAX_LENGTH"]
    )
    description = validator.string(
        data, "description", required=False, max_length=current_app.config["TEXT_MAX_LENGTH"]
    )
    status = validator.choice(
        data, "status", TaskStatus.ALL, required=False, default=TaskStatus.PENDING
    )
    validator.raise_if_errors()

    task = Task(title=title, description=description, status=status, project=project)
    db.session.add(task)
    db.session.commit()

    return jsonify({"task": task.to_dict()}), 201
