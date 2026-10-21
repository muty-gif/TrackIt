"""Dashboard metrics and quick-access lists for the current user."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

from flask import Blueprint, g, jsonify
from sqlalchemy import case, func

from ..auth.utils import login_required
from ..extensions import db
from ..models import Project, Task, TaskStatus

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api")


def _utc(value: datetime) -> datetime:
    """Normalise SQLite's naive datetimes so recent items sort safely."""
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


@dashboard_bp.get("/dashboard")
@login_required
def get_dashboard():
    owner_id = g.current_user.id
    now = datetime.now(timezone.utc)
    today = now.date()
    week_start = datetime.combine(
        today - timedelta(days=today.weekday()), time.min, tzinfo=timezone.utc
    )

    project_count = db.session.scalar(
        db.select(func.count(Project.id)).where(Project.owner_id == owner_id)
    )

    task_totals = db.session.execute(
        db.select(
            func.count(Task.id),
            func.coalesce(
                func.sum(case((Task.status != TaskStatus.COMPLETED, 1), else_=0)), 0
            ),
            func.coalesce(
                func.sum(
                    case(
                        (
                            (Task.status == TaskStatus.COMPLETED)
                            & (Task.completed_at >= week_start),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ),
            func.coalesce(
                func.sum(
                    case(
                        (
                            (Task.status != TaskStatus.COMPLETED)
                            & (Task.due_date.is_not(None))
                            & (Task.due_date < today),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ),
            func.coalesce(
                func.sum(
                    case(
                        (
                            (Task.status != TaskStatus.COMPLETED)
                            & (Task.due_date == today),
                            1,
                        ),
                        else_=0,
                    )
                ),
                0,
            ),
        )
        .join(Project, Task.project_id == Project.id)
        .where(Project.owner_id == owner_id)
    ).one()
    _, open_tasks, completed_this_week, overdue, due_today = task_totals

    status_counts = {
        status: 0 for status in TaskStatus.ALL
    }
    status_rows = db.session.execute(
        db.select(Task.status, func.count(Task.id))
        .join(Project, Task.project_id == Project.id)
        .where(Project.owner_id == owner_id)
        .group_by(Task.status)
    ).all()
    for status, count in status_rows:
        status_counts[status] = count

    completed = func.coalesce(
        func.sum(case((Task.status == TaskStatus.COMPLETED, 1), else_=0)), 0
    )
    project_rows = db.session.execute(
        db.select(Project, func.count(Task.id), completed)
        .outerjoin(Task, Task.project_id == Project.id)
        .where(Project.owner_id == owner_id)
        .group_by(Project.id)
        .order_by(Project.updated_at.desc(), Project.id.desc())
    ).all()
    projects = [
        project.to_dict(task_count=task_count, completed_task_count=completed_count)
        for project, task_count, completed_count in project_rows
    ]

    upcoming_rows = db.session.execute(
        db.select(Task, Project.name)
        .join(Project, Task.project_id == Project.id)
        .where(
            Project.owner_id == owner_id,
            Task.status != TaskStatus.COMPLETED,
            Task.due_date.is_not(None),
            Task.due_date >= today,
        )
        .order_by(Task.due_date.asc(), Task.id.asc())
        .limit(5)
    ).all()
    upcoming = [
        {**task.to_dict(), "project_name": project_name}
        for task, project_name in upcoming_rows
    ]

    recent_projects = db.session.execute(
        db.select(Project)
        .where(Project.owner_id == owner_id)
        .order_by(Project.updated_at.desc(), Project.id.desc())
        .limit(5)
    ).scalars()
    recent_tasks = db.session.execute(
        db.select(Task, Project.name)
        .join(Project, Task.project_id == Project.id)
        .where(Project.owner_id == owner_id)
        .order_by(Task.updated_at.desc(), Task.id.desc())
        .limit(5)
    ).all()

    recent: list[tuple[datetime, dict]] = []
    for project in recent_projects:
        recent.append(
            (
                _utc(project.updated_at),
                {
                    "kind": "project",
                    "id": project.id,
                    "title": project.name,
                    "project_id": project.id,
                    "project_name": project.name,
                    "status": None,
                    "due_date": project.due_date.isoformat() if project.due_date else None,
                    "updated_at": project.updated_at.isoformat(),
                },
            )
        )
    for task, project_name in recent_tasks:
        recent.append(
            (
                _utc(task.updated_at),
                {
                    "kind": "task",
                    "id": task.id,
                    "title": task.title,
                    "project_id": task.project_id,
                    "project_name": project_name,
                    "status": task.status,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "updated_at": task.updated_at.isoformat(),
                },
            )
        )
    recent.sort(key=lambda item: item[0], reverse=True)

    return jsonify(
        {
            "metrics": {
                "project_count": project_count or 0,
                "open_task_count": int(open_tasks or 0),
                "completed_this_week": int(completed_this_week or 0),
                "overdue_task_count": int(overdue or 0),
                "due_today_count": int(due_today or 0),
            },
            "status_counts": status_counts,
            "projects": projects,
            "upcoming": upcoming,
            "recent": [item for _, item in recent[:6]],
        }
    )
