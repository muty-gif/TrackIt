# TrackIt

Flask + SQLAlchemy JSON API with a plain HTML/CSS/ES-module frontend. `README.md`
is the human setup/API/deploy reference; `USE-CASES.md` is the behaviour spec.

## Commands

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
flask db upgrade                           # create/update the DB (default: instance/trackit.sqlite3)
flask run                                  # dev server, or: python app.py
python -m unittest discover -v             # full suite (in-memory SQLite)
python -m unittest tests.test_auth.RegisterTests.test_email_is_normalised -v  # single test
npm run build                              # gate: `neon config plan` + unittest suite
```

- There is no linter, typechecker, or CI. Tests are the only automated check.
- `npm run build` is not a JS build: the frontend has no bundling step. It runs
  the Neon CLI (`neon config plan`, needs a linked branch) plus the Python tests.
  For Python-only changes, run `unittest` directly.
- Run commands from the repo root; `config.py` is a top-level import used by
  `migrations/env.py`.

## Architecture

- `trackit.create_app()` in `trackit/__init__.py` builds the app; `app.py` is the
  dev entry point, `wsgi.py` the production one (gunicorn).
- Blueprints: `auth/` (register/login/logout/me), `dashboard/`
  (`GET /api/dashboard` metrics and quick lists), `projects/` (project CRUD and
  nested task list/create), `tasks/` (task get/patch/delete), `main/` (HTML page
  shells and page-level redirect guards). All JSON routes live under `/api/`.
- `/` renders the dashboard for logged-in users and redirects anonymous visitors
  to `/login`; `/projects` and `/projects/<id>` are the project views.
- `access.py` handles ownership: a missing row and another user's row both raise
  `NotFoundError` (404) so existence is not leaked. Do not add separate 403 paths.
- `errors.py` defines the `ApiError` hierarchy. API errors always return
  `{"error": {"code", "message", "fields"?}}`; page routes keep Flask's HTML
  errors. `validation.py` collects all field errors into one 422 response.
- Auth is a signed `HttpOnly` session cookie and `g.current_user`; there are no
  API tokens and no CSRF token.
- The frontend is Jinja shells in `templates/` plus ES modules in `static/js/`;
  shared design tokens and dark-mode overrides live in `static/css/styles.css`.
  `static/js/theme.js` runs before first paint; do not convert it to a module.
- `gunicorn ... wsgi:app` requires `flask db upgrade` first; see `Procfile`,
  `render.yaml`, `railway.json`.

## Database / Neon

- `.env.local` (written by `neon deploy`, git-ignored) overrides `.env`; real
  environment variables override both. Because `migrations/env.py` imports
  `config`, a local `flask db upgrade` will target the linked Neon database via
  `DATABASE_URL_UNPOOLED` unless you unset it and set `DATABASE_URL` explicitly.
- `DATABASE_URL` is the pooled app connection; migrations automatically prefer
  `DATABASE_URL_UNPOOLED` (direct). Alembic cannot run through Neon's pooler.
- Managed Postgres URLs are rewritten to `postgresql+psycopg://` by
  `config.normalize_database_url()`; `psycopg[binary]` is the driver.
- Tests use `tests.base.BaseTestCase`, which overrides the DB to in-memory
  SQLite and calls `db.create_all()`. They do not exercise migrations, so after
  changing models run `flask db migrate -m "describe change"` and `flask db upgrade`.
- `.neon` (org/project/branch link) is git-ignored; a fresh clone needs relinking
  before Neon commands work.

## Domain rules

- Task `status` is `pending`, `in_progress` or `completed` (`TaskStatus`);
  `priority` is `low`, `medium` or `high`; `due_date` is a `Date` or null.
  `completed_at` is maintained by the PATCH route, not by clients.
- Changing a task's `project_id` is rejected with 422.
- Deleting a project cascades to its tasks (ORM plus `ON DELETE CASCADE`).
- Cross-user isolation is the core invariant: every project/task lookup must go
  through `access.py` or apply the equivalent owner check.
