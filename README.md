# TrackIt

TrackIt is a small web application where registered users manage personal
projects and the tasks inside them. Each project belongs to exactly one user and
each task belongs to exactly one project; users can never see or change another
user's data.

The behaviour implemented here is described in [`USE-CASES.md`](USE-CASES.md).

## Stack

**Backend** — Python, Flask, Flask Blueprints, SQLAlchemy (via Flask-SQLAlchemy),
Flask-Migrate, a JSON REST API.

**Frontend** — plain HTML, CSS and JavaScript using `fetch()`, JSON and the DOM.
No build step and no front-end framework: the server delivers HTML shells and the
browser fills them in from the API.

## Project layout

```
TrackIt/
├── app.py                     # entry point (python app.py / flask run)
├── config.py                  # configuration (env-overridable)
├── trackit/
│   ├── __init__.py            # create_app factory
│   ├── extensions.py          # db + migrate singletons
│   ├── models.py              # User, Project, Task
│   ├── errors.py              # ApiError types + JSON error handlers
│   ├── validation.py          # request/field validation
│   ├── access.py              # ownership lookups ("not found" for foreign rows)
│   ├── auth/                  # blueprint: register / login / logout / me
│   ├── projects/              # blueprint: project CRUD + nested task list/create
│   ├── tasks/                 # blueprint: task read / update / delete
│   └── main/                  # blueprint: HTML page shells + page guards
├── templates/                 # HTML shells (login, register, projects, project)
├── static/
│   ├── css/styles.css
│   └── js/                    # api.js, ui.js, nav.js + one module per page
├── migrations/                # Alembic migrations managed by Flask-Migrate
├── tests/                     # unittest suite (52 tests)
├── USE-CASES.md               # requirements / use case specification
├── requirements.txt
└── .env.example
```

## Getting started

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # optional in development

flask db upgrade              # create the SQLite database (instance/trackit.sqlite3)
flask run                     # http://127.0.0.1:5000
```

Open the site, click **Create one**, register, and start adding projects and tasks.

## Running the tests

```bash
python -m unittest discover -v
```

The suite runs against an in-memory SQLite database and covers registration,
login, logout, project and task CRUD, validation, cascade deletion and — most
importantly — cross-user isolation.

## API reference

All endpoints exchange JSON. Authentication uses an `HttpOnly` session cookie, so
browser requests must be same-origin (the bundled front end is).

Error responses always look like:

```json
{ "error": { "code": "validation_error", "message": "Validation failed.",
             "fields": { "name": "This field is required." } } }
```

### Auth

| Method | Path | Auth | Body | Success |
|---|---|---|---|---|
| POST | `/api/auth/register` | – | `{email, password}` | `201` `{user}` |
| POST | `/api/auth/login` | – | `{email, password}` | `200` `{user}` |
| POST | `/api/auth/logout` | yes | – | `204` |
| GET | `/api/auth/me` | yes | – | `200` `{user}` |

### Projects

| Method | Path | Body | Success |
|---|---|---|---|
| GET | `/api/projects` | – | `200` `{projects: [...]}` (with task counters) |
| POST | `/api/projects` | `{name, description?}` | `201` `{project}` |
| GET | `/api/projects/<id>` | – | `200` `{project}` (includes tasks) |
| PATCH | `/api/projects/<id>` | `{name?, description?}` | `200` `{project}` |
| DELETE | `/api/projects/<id>` | – | `204` (cascades to tasks) |
| GET | `/api/projects/<id>/tasks` | – | `200` `{tasks: [...]}` |
| POST | `/api/projects/<id>/tasks` | `{title, description?, status?}` | `201` `{task}` |

### Tasks

| Method | Path | Body | Success |
|---|---|---|---|
| GET | `/api/tasks/<id>` | – | `200` `{task}` |
| PATCH | `/api/tasks/<id>` | `{title?, description?, status?}` | `200` `{task}` |
| DELETE | `/api/tasks/<id>` | – | `204` |

`status` is either `pending` (default) or `completed`. A task's `project_id`
cannot be changed; attempts return `422`.

## Data model

- **User** — `id`, unique `email` (stored lower-cased), `password_hash`, `created_at`.
- **Project** — `id`, `name`, `description`, `owner_id` → `users.id`, timestamps.
- **Task** — `id`, `title`, `description`, `status`, `project_id` → `projects.id`,
  timestamps.

Deleting a user or a project cascades to its projects/tasks (also enforced at the
database level with `ON DELETE CASCADE`).

## Behaviour decisions

These resolve the open questions raised in `USE-CASES.md`:

| Topic | Decision |
|---|---|
| Another user's resource | Treated as **`404 Not Found`** so the resource's existence is never leaked. The ownership check still distinguishes the cases internally. |
| Not authenticated | API → `401` with code `unauthorized`; pages → redirect to `/login` (remembering `?next=`). |
| Validation failure | `422` with code `validation_error` and a `fields` map. Malformed/non-JSON bodies → `400` / `415`. |
| Duplicate email | `409` with an explicit "already exists" message. |
| Bad login | `401` with a single generic message for unknown email *and* wrong password. |
| Registration | The new user is logged in immediately. |
| Deleting a project | Deletes its tasks (cascade). |
| Task status | Two values only: `pending` / `completed`. Marking is idempotent. |
| Task project | Immutable — a task cannot be moved between projects. |
| Session | Signed cookie, `HttpOnly`, `SameSite=Lax`, 7-day lifetime. |

## Notes / non-goals

- SQLite is the default database for convenience; set `DATABASE_URL` to use
  PostgreSQL or MySQL. Remember to run `flask db upgrade` afterwards.
- Set a strong `SECRET_KEY` and `SESSION_COOKIE_SECURE=1` in production.
- Password reset, email verification, task filtering/pagination and account
  management beyond viewing the current user are intentionally out of scope
  (they are listed as candidate additions in `USE-CASES.md`).
