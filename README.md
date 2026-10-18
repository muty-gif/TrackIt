# TrackIt

TrackIt is a small web application where registered users manage personal
projects and the tasks inside them. Each project belongs to exactly one user and
each task belongs to exactly one project; users can never see or change another
user's data.

The behaviour implemented here is described in [`USE-CASES.md`](USE-CASES.md).

## Screenshots

**Sign in and register**

| Log in | Register |
|---|---|
| ![Log in page](docs/screenshots/01-login.png) | ![Registration page](docs/screenshots/02-register.png) |

**Projects**

| Create a project | Project list |
|---|---|
| ![New project form filled in](docs/screenshots/03-new-project.png) | ![Projects list showing one project](docs/screenshots/04-projects.png) |

**Tasks**

| Add a task | Track progress |
|---|---|
| ![New task form filled in](docs/screenshots/05-new-task.png) | ![Task list with two tasks completed](docs/screenshots/06-tasks.png) |

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
├── tests/                     # unittest suite (57 tests)
├── docs/screenshots/          # screenshots used in this README
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

## Neon (the configured database)

This project is linked to a Neon project: `neon.ts` declares the services and
`.neon` records the project/branch. `neon deploy` writes the connection strings
into `.env.local` (git-ignored):

| Variable | Used by | Connection |
|---|---|---|
| `DATABASE_URL` | the application | **pooled** (host contains `-pooler`) |
| `DATABASE_URL_UNPOOLED` | `flask db upgrade` (Alembic) | **direct** |

Migrations must use the **direct** connection: Neon's pooler runs PgBouncer in
transaction mode, which does not support the session-level state Alembic relies
on. `config.py` loads `.env.local` before `.env` (without overriding real
environment variables), and `migrations/env.py` automatically prefers
`DATABASE_URL_UNPOOLED` when it is set. Both URLs are normalised to the
`postgresql+psycopg://` driver.

```bash
neon deploy        # apply neon.ts to the branch and refresh .env.local
flask db upgrade   # migrate the Neon database (direct connection)
npm run build      # gate: `neon config plan` + the Flask test suite
```

There is no JavaScript bundling step — the front end is plain HTML/CSS/JS served
by Flask — so `npm run build` acts as the gate for the Neon config and the Python
test suite instead.

## Deploying

The Flask development server is for local use only. In production, serve the
app with a real WSGI server (`gunicorn`) — the platform or a reverse proxy should
handle HTTPS.

### 1. Decide on the database first

SQLite (the default) is fine for a single small instance **only if the disk
persists** between deploys. Most PaaS filesystems are ephemeral, so point
`DATABASE_URL` at a managed PostgreSQL database:

```
DATABASE_URL=postgresql+psycopg://user:password@host:5432/trackit
```

Managed hosts hand out `postgres://`-style URLs; `config.normalize_database_url()`
rewrites them to the `postgresql+psycopg://` scheme automatically, and the driver
(`psycopg[binary]`) is already in `requirements.txt`.

### 2. Set production environment variables

| Variable | Value |
|---|---|
| `SECRET_KEY` | a long random string — `python -c "import secrets;print(secrets.token_hex(32))"` |
| `DATABASE_URL` | your database connection string |
| `SESSION_COOKIE_SECURE` | `1` (cookie sent over HTTPS only) |
| `TRUST_PROXY` | `1` when behind a reverse proxy / load balancer |
| `PASSWORD_MIN_LENGTH` | optional, defaults to `8` |

### 3. Migrate, then start

```bash
flask db upgrade                                   # run on every release
gunicorn --bind 0.0.0.0:$PORT --workers 3 wsgi:app # start the app
```

The bundled `Procfile` does the same on platforms that read one (Heroku,
Railway):

```
release: flask db upgrade
web: gunicorn --bind 0.0.0.0:$PORT --workers 3 --timeout 60 --access-logfile - wsgi:app
```

### Free hosting that does not expire

`render.yaml` and `railway.json` are ready-made for the two hosts worth using;
pair either with a permanent free Postgres.

| Service | Free tier | Expires? |
|---|---|---|
| **Neon** (Postgres) | 0.5 GB, 100 compute-hours/month; suspends after ~5 min idle, wakes on demand | **No** — permanent |
| **Render** (web service) | 750 instance-hours/month; spins down after ~15 min idle | **No** — persists |
| **Supabase** (Postgres) | 500 MB; pauses after ~1 week idle, data retained | **No** — pauses |
| **Render** (Postgres) | 1 GB | **Yes** — deleted 30 days after creation |
| **Railway** | One-off trial credit | **Yes** — no permanent free DB |

So the long-lived free recipe is **Neon (database) + Render (web service)**:

- **Neon** — sign up at [neon.com](https://neon.com), create a project, and copy
  the connection string (it looks like
  `postgresql://user:password@ep-xxx.aws.neon.tech/neondb?sslmode=require`).
- **Render** — *New → Blueprint*, pick the repo, and paste the Neon URL when
  prompted for `DATABASE_URL`. The start command migrates then starts gunicorn,
  and HTTPS is automatic. To use a Render-managed database instead, uncomment the
  `databases:` block in `render.yaml` — but it is deleted after 30 days.
- **Railway** — *New Project → Deploy from GitHub repo*, add the step 2 variables
  under **Variables**, then *Settings → Networking → Generate Domain*.
- **Anywhere else** — `pip install -r requirements.txt`, `flask db upgrade`,
  `gunicorn --bind 0.0.0.0:$PORT --workers 3 wsgi:app`. On a VPS, run gunicorn on
  `127.0.0.1:8000` behind nginx + TLS and set `TRUST_PROXY=1`; in Docker, base on
  `python:3.12-slim` and run the same three commands.

### Production checklist

- [ ] `SECRET_KEY` set to a random value (never the default).
- [ ] `SESSION_COOKIE_SECURE=1` and the site served over HTTPS.
- [ ] `TRUST_PROXY=1` if a proxy terminates TLS.
- [ ] `DATABASE_URL` points to a persistent database; `flask db upgrade` runs on deploy.
- [ ] Debug mode is off (do not run `python app.py` in production).
- [ ] Backups configured for the database.

## Notes / non-goals

- SQLite is the default database for convenience; set `DATABASE_URL` to use
  PostgreSQL or MySQL. Remember to run `flask db upgrade` afterwards.
- Set a strong `SECRET_KEY` and `SESSION_COOKIE_SECURE=1` in production.
- Password reset, email verification, task filtering/pagination and account
  management beyond viewing the current user are intentionally out of scope
  (they are listed as candidate additions in `USE-CASES.md`).
