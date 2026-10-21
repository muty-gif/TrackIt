"""TrackIt application factory.

Wires together configuration, extensions, blueprints and error handling.
"""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask

from . import models  # noqa: F401  (ensures model metadata is registered)
from .errors import register_error_handlers
from .extensions import db, migrate

BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"


def create_app(config_object="config.Config", overrides: dict | None = None) -> Flask:
    """Create and configure a Flask application instance."""
    app = Flask(
        __name__,
        instance_path=str(INSTANCE_DIR),
        instance_relative_config=True,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )
    app.config.from_object(config_object)
    if overrides:
        app.config.update(overrides)

    if app.config.get("TRUST_PROXY"):
        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)

    from .auth.utils import init_app as init_auth
    from .auth.routes import auth_bp
    from .dashboard.routes import dashboard_bp
    from .main.routes import main_bp
    from .projects.routes import projects_bp
    from .tasks.routes import tasks_bp

    init_auth(app)

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(tasks_bp)

    register_error_handlers(app)

    return app
