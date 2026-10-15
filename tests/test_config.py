"""Configuration helpers (database URL normalisation)."""

from __future__ import annotations

from config import normalize_database_url
from tests.base import BaseTestCase


class DatabaseUrlTests(BaseTestCase):
    def test_postgres_scheme_is_rewritten_to_psycopg(self):
        url = "postgres://user:secret@host:5432/trackit"
        self.assertEqual(
            normalize_database_url(url),
            "postgresql+psycopg://user:secret@host:5432/trackit",
        )

    def test_postgresql_scheme_is_rewritten_to_psycopg(self):
        url = "postgresql://user:secret@host:5432/trackit"
        self.assertEqual(
            normalize_database_url(url),
            "postgresql+psycopg://user:secret@host:5432/trackit",
        )

    def test_already_normalised_url_is_untouched(self):
        url = "postgresql+psycopg://user:secret@host:5432/trackit"
        self.assertEqual(normalize_database_url(url), url)

    def test_sqlite_url_is_untouched(self):
        url = "sqlite:///instance/trackit.sqlite3"
        self.assertEqual(normalize_database_url(url), url)

    def test_connection_options_are_preserved(self):
        """Providers like Neon append ?sslmode=require — it must survive."""
        url = "postgresql://user:secret@ep-cool-1.aws.neon.tech/neondb?sslmode=require"
        self.assertEqual(
            normalize_database_url(url),
            "postgresql+psycopg://user:secret@ep-cool-1.aws.neon.tech/neondb?sslmode=require",
        )
