"""SQLAlchemy models: User, Project and Task.

Ownership rules mirrored from USE-CASES.md:
  * a User owns many Projects;
  * a Project belongs to exactly one User;
  * a Task belongs to exactly one Project;
  * deleting a Project deletes its Tasks (cascade).
"""

from __future__ import annotations

from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


class TaskStatus:
    """Allowed values for ``Task.status``."""

    PENDING = "pending"
    COMPLETED = "completed"
    ALL = (PENDING, COMPLETED)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    projects = db.relationship(
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan",
        order_by="Project.created_at",
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "created_at": _iso(self.created_at),
        }


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    owner_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    owner = db.relationship("User", back_populates="projects")
    tasks = db.relationship(
        "Task",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Task.created_at",
    )

    def to_dict(
        self,
        *,
        include_tasks: bool = False,
        task_count: int | None = None,
        completed_task_count: int | None = None,
    ) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": _iso(self.created_at),
            "updated_at": _iso(self.updated_at),
        }
        if task_count is not None:
            data["task_count"] = int(task_count)
            data["completed_task_count"] = int(completed_task_count or 0)
        if include_tasks:
            data["tasks"] = [task.to_dict() for task in self.tasks]
        return data


class Task(db.Model):
    __tablename__ = "tasks"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('pending', 'completed')", name="ck_tasks_status"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default=TaskStatus.PENDING)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    project = db.relationship("Project", back_populates="tasks")

    @property
    def is_completed(self) -> bool:
        return self.status == TaskStatus.COMPLETED

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "is_completed": self.is_completed,
            "project_id": self.project_id,
            "created_at": _iso(self.created_at),
            "updated_at": _iso(self.updated_at),
        }
