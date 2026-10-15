"""Application configuration.

Every value can be overridden with an environment variable (see ``.env.example``).
The defaults are safe for local development.
"""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"

load_dotenv(BASE_DIR / ".env")


class Config:
    """Base configuration consumed by the application factory."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    # --- Database -----------------------------------------------------------
    # SQLite by default; point DATABASE_URL at PostgreSQL/MySQL in production.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{INSTANCE_DIR / 'trackit.sqlite3'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # --- Session / cookies --------------------------------------------------
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
    PERMANENT_SESSION_LIFETIME = timedelta(
        seconds=int(os.environ.get("SESSION_LIFETIME_SECONDS", 60 * 60 * 24 * 7))
    )

    # --- Domain rules -------------------------------------------------------
    PASSWORD_MIN_LENGTH = int(os.environ.get("PASSWORD_MIN_LENGTH", 8))
    PASSWORD_MAX_LENGTH = 128
    PROJECT_NAME_MAX_LENGTH = 120
    TASK_TITLE_MAX_LENGTH = 200
    TEXT_MAX_LENGTH = 5000

    JSON_SORT_KEYS = False
