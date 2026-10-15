"""Session helpers and the ``login_required`` guard."""

from __future__ import annotations

from functools import wraps

from flask import g, session

from ..errors import UnauthorizedError
from ..extensions import db
from ..models import User


def get_current_user() -> User | None:
    """Resolve the logged-in user from the session, or ``None``."""
    user_id = session.get("user_id")
    if user_id is None:
        return None
    user = db.session.get(User, user_id)
    if user is None:
        # Stale session pointing at a deleted account.
        session.clear()
    return user


def login_user(user: User) -> None:
    session.clear()
    session["user_id"] = user.id
    session.permanent = True
    g.current_user = user


def logout_user() -> None:
    session.clear()
    g.current_user = None


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if getattr(g, "current_user", None) is None:
            raise UnauthorizedError()
        return view(*args, **kwargs)

    return wrapper


def init_app(app) -> None:  # noqa: ANN001
    @app.before_request
    def _load_current_user() -> None:
        g.current_user = get_current_user()
