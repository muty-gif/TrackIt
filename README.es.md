# TrackIt

[English](README.md) | **Español**

TrackIt es una pequeña aplicación web en la que los usuarios registrados gestionan
proyectos personales y las tareas que contienen. Cada proyecto pertenece a
exactamente un usuario y cada tarea pertenece a exactamente un proyecto; los
usuarios nunca pueden ver ni modificar los datos de otro usuario.

El comportamiento implementado aquí se describe en [`USE-CASES.md`](USE-CASES.md).

## Capturas de pantalla

**Panel**

![Panel con métricas, gráfico de estados y progreso de proyectos](docs/screenshots/dashboard.png)

**Iniciar sesión y registrarse**

| Iniciar sesión | Registrarse |
|---|---|
| ![Página de inicio de sesión](docs/screenshots/login.png) | ![Página de registro](docs/screenshots/register.png) |

**Proyectos**

| Espacio vacío | Diálogo de nuevo proyecto |
|---|---|
| ![Página de proyectos vacía](docs/screenshots/projects-empty.png) | ![Diálogo para crear un proyecto con nombre, descripción y fecha](docs/screenshots/new-project.png) |

| Listado de proyectos | Espacio de trabajo |
|---|---|
| ![Listado con una tarjeta de proyecto y su progreso](docs/screenshots/projects.png) | ![Página de proyecto con tareas, filtros y controles en línea](docs/screenshots/project.png) |

**Tareas**

![Listado de tareas con controles de estado, prioridad y fecha](docs/screenshots/tasks.png)

## Vídeos de demostración

Grabaciones breves de la interfaz rediseñada:

- [Recorrido por el panel](docs/videos/dashboard-tour.mp4)
- [Controles de proyecto y tareas](docs/videos/project-tasks-tour.mp4)

## Stack

**Backend** — Python, Flask, Flask Blueprints, SQLAlchemy (mediante
Flask-SQLAlchemy), Flask-Migrate, una API REST con JSON.

**Frontend** — HTML, CSS y JavaScript básicos usando `fetch()`, JSON y el DOM.
Sin paso de compilación ni framework de front-end: el servidor entrega las
plantillas HTML y el navegador las rellena desde la API.

## Estructura del proyecto

```
TrackIt/
├── app.py                     # punto de entrada (python app.py / flask run)
├── config.py                  # configuración (sobrescribible por entorno)
├── trackit/
│   ├── __init__.py            # fábrica create_app
│   ├── extensions.py          # instancias de db + migrate
│   ├── models.py              # User, Project, Task
│   ├── errors.py              # tipos ApiError + manejadores de errores JSON
│   ├── validation.py          # validación de peticiones/campos
│   ├── access.py              # comprobación de propiedad ("no encontrado" para filas ajenas)
│   ├── auth/                  # blueprint: register / login / logout / me
│   ├── dashboard/             # blueprint: métricas del panel + listas rápidas
│   ├── projects/              # blueprint: CRUD de proyectos + listado/creación de tareas anidadas
│   ├── tasks/                 # blueprint: lectura / actualización / borrado de tareas
│   └── main/                  # blueprint: plantillas HTML + protecciones de página
├── templates/                 # plantillas HTML (dashboard, login, register, projects, project)
├── static/
│   ├── css/styles.css
│   └── js/                    # api.js, ui.js, nav.js + un módulo por página
├── migrations/                # migraciones de Alembic gestionadas por Flask-Migrate
├── tests/                     # suite unittest (70 pruebas)
├── docs/
│   ├── screenshots/           # capturas usadas en este README
│   └── videos/                # grabaciones breves de demostración
├── USE-CASES.md               # especificación de requisitos / casos de uso
├── requirements.txt
└── .env.example
```

## Puesta en marcha

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # opcional en desarrollo

flask db upgrade              # crea la base de datos SQLite (instance/trackit.sqlite3)
flask run                     # http://127.0.0.1:5000
```

Abre la web, pulsa **Create one**, regístrate y empieza a añadir proyectos y tareas.

## Ejecutar las pruebas

```bash
python -m unittest discover -v
```

La suite se ejecuta contra una base de datos SQLite en memoria y cubre el registro,
el inicio y cierre de sesión, el CRUD de proyectos y tareas, la validación, el
borrado en cascada y — lo más importante — el aislamiento entre usuarios.

## Referencia de la API

Todos los endpoints intercambian JSON. La autenticación usa una cookie de sesión
`HttpOnly`, por lo que las peticiones del navegador deben ser del mismo origen (el
front-end incluido lo es).

Las respuestas de error siempre tienen esta forma:

```json
{ "error": { "code": "validation_error", "message": "Validation failed.",
             "fields": { "name": "This field is required." } } }
```

### Panel

| Método | Ruta | Auth | Éxito |
|---|---|---|---|
| GET | `/api/dashboard` | sí | `200` `{metrics, status_counts, projects, upcoming, recent}` |

`metrics` contiene `project_count`, `open_task_count`, `completed_this_week`,
`overdue_task_count` y `due_today_count`. `status_counts` siempre incluye
`pending`, `in_progress` y `completed`.

### Autenticación

| Método | Ruta | Auth | Cuerpo | Éxito |
|---|---|---|---|---|
| POST | `/api/auth/register` | – | `{email, password}` | `201` `{user}` |
| POST | `/api/auth/login` | – | `{email, password}` | `200` `{user}` |
| POST | `/api/auth/logout` | sí | – | `204` |
| GET | `/api/auth/me` | sí | – | `200` `{user}` |

### Proyectos

| Método | Ruta | Cuerpo | Éxito |
|---|---|---|---|
| GET | `/api/projects` | – | `200` `{projects: [...]}` (con contadores de tareas) |
| POST | `/api/projects` | `{name, description?, due_date?}` | `201` `{project}` |
| GET | `/api/projects/<id>` | – | `200` `{project}` (incluye las tareas) |
| PATCH | `/api/projects/<id>` | `{name?, description?, due_date?}` | `200` `{project}` |
| DELETE | `/api/projects/<id>` | – | `204` (en cascada a las tareas) |
| GET | `/api/projects/<id>/tasks` | – | `200` `{tasks: [...]}` |
| POST | `/api/projects/<id>/tasks` | `{title, description?, status?, priority?, due_date?}` | `201` `{task}` |

### Tareas

| Método | Ruta | Cuerpo | Éxito |
|---|---|---|---|
| GET | `/api/tasks/<id>` | – | `200` `{task}` |
| PATCH | `/api/tasks/<id>` | `{title?, description?, status?, priority?, due_date?}` | `200` `{task}` |
| DELETE | `/api/tasks/<id>` | – | `204` |

`status` es `pending` (por defecto), `in_progress` o `completed`. `priority` es
`low`, `medium` (por defecto) o `high`. `due_date` es una fecha ISO
(`YYYY-MM-DD`) o `null`; las fechas de proyecto usan el mismo formato.
`completed_at` se rellena al completar una tarea y se borra al reabrirla. El
`project_id` de una tarea no se puede cambiar; los intentos devuelven `422`.

## Modelo de datos

- **User** — `id`, `email` único (guardado en minúsculas), `password_hash`,
  `created_at`.
- **Project** — `id`, `name`, `description`, `due_date`, `owner_id` → `users.id`, marcas de
  tiempo.
- **Task** — `id`, `title`, `description`, `status`, `priority`, `due_date`,
  `completed_at`, `project_id` → `projects.id`, marcas de tiempo.

Borrar un usuario o un proyecto se propaga en cascada a sus proyectos/tareas
(también se aplica a nivel de base de datos con `ON DELETE CASCADE`).

## Decisiones de comportamiento

Estas resuelven las preguntas abiertas planteadas en `USE-CASES.md`:

| Tema | Decisión |
|---|---|
| Recurso de otro usuario | Se trata como **`404 Not Found`** para no filtrar nunca la existencia del recurso. La comprobación de propiedad sigue distinguiendo los casos internamente. |
| No autenticado | API → `401` con el código `unauthorized`; páginas → redirección a `/login` (recordando `?next=`). |
| Fallo de validación | `422` con el código `validation_error` y un mapa `fields`. Cuerpos mal formados o no JSON → `400` / `415`. |
| Email duplicado | `409` con un mensaje explícito de "ya existe". |
| Login incorrecto | `401` con un único mensaje genérico tanto para email desconocido *como* para contraseña incorrecta. |
| Registro | El nuevo usuario inicia sesión inmediatamente. |
| Borrar un proyecto | Borra sus tareas (en cascada). |
| Estado de la tarea | `pending`, `in_progress` o `completed`. Marcarla es idempotente. |
| Prioridad de la tarea | `low`, `medium` (por defecto) o `high`. |
| Fechas de vencimiento | Fechas opcionales; el panel ignora las tareas completadas para vencidas/próximas. |
| Proyecto de la tarea | Inmutable — una tarea no se puede mover entre proyectos. |
| Sesión | Cookie firmada, `HttpOnly`, `SameSite=Lax`, duración de 7 días. |

## Neon (la base de datos configurada)

Este proyecto está vinculado a un proyecto de Neon: `neon.ts` declara los servicios
y `.neon` registra el proyecto/rama. `neon deploy` escribe las cadenas de conexión
en `.env.local` (ignorado por git):

| Variable | Usada por | Conexión |
|---|---|---|
| `DATABASE_URL` | la aplicación | **con pool** (el host contiene `-pooler`) |
| `DATABASE_URL_UNPOOLED` | `flask db upgrade` (Alembic) | **directa** |

Las migraciones deben usar la conexión **directa**: el pooler de Neon ejecuta
PgBouncer en modo transacción, que no admite el estado a nivel de sesión del que
depende Alembic. `config.py` carga `.env.local` antes que `.env` (sin sobrescribir
las variables de entorno reales), y `migrations/env.py` prefiere automáticamente
`DATABASE_URL_UNPOOLED` cuando está definida. Ambas URLs se normalizan al driver
`postgresql+psycopg://`.

```bash
neon deploy        # aplica neon.ts a la rama y refresca .env.local
flask db upgrade   # migra la base de datos de Neon (conexión directa)
npm run build      # verificación: `neon config plan` + la suite de pruebas de Flask
```

No hay paso de empaquetado de JavaScript — el front-end es HTML/CSS/JS básico
servido por Flask —, así que `npm run build` actúa como verificación de la
configuración de Neon y de la suite de pruebas de Python.

## Despliegue

El servidor de desarrollo de Flask es solo para uso local. En producción, sirve la
aplicación con un servidor WSGI real (`gunicorn`) — la plataforma o un proxy inverso
debería encargarse de HTTPS.

### 1. Decide primero la base de datos

SQLite (el valor por defecto) sirve para una única instancia pequeña **solo si el
disco persiste** entre despliegues. La mayoría de los sistemas de archivos de PaaS
son efímeros, así que apunta `DATABASE_URL` a una base de datos PostgreSQL
gestionada:

```
DATABASE_URL=postgresql+psycopg://user:password@host:5432/trackit
```

Los proveedores gestionados entregan URLs del estilo `postgres://`;
`config.normalize_database_url()` las reescribe automáticamente al esquema
`postgresql+psycopg://`, y el driver (`psycopg[binary]`) ya está en
`requirements.txt`.

### 2. Define las variables de entorno de producción

| Variable | Valor |
|---|---|
| `SECRET_KEY` | una cadena aleatoria larga — `python -c "import secrets;print(secrets.token_hex(32))"` |
| `DATABASE_URL` | tu cadena de conexión a la base de datos |
| `SESSION_COOKIE_SECURE` | `1` (la cookie se envía solo por HTTPS) |
| `TRUST_PROXY` | `1` cuando hay un proxy inverso / balanceador de carga delante |
| `PASSWORD_MIN_LENGTH` | opcional, por defecto `8` |

### 3. Migra y luego arranca

```bash
flask db upgrade                                   # ejecútalo en cada despliegue
gunicorn --bind 0.0.0.0:$PORT --workers 3 wsgi:app # arranca la aplicación
```

El `Procfile` incluido hace lo mismo en las plataformas que lo leen (Heroku,
Railway):

```
release: flask db upgrade
web: gunicorn --bind 0.0.0.0:$PORT --workers 3 --timeout 60 --access-logfile - wsgi:app
```

### Hosting gratuito que no caduca

`render.yaml` y `railway.json` están listos para los dos hosts que merecen la pena;
combina cualquiera de ellos con un Postgres gratuito permanente.

| Servicio | Plan gratuito | ¿Caduca? |
|---|---|---|
| **Neon** (Postgres) | 0,5 GB, 100 horas de cómputo/mes; se suspende tras ~5 min inactivo y se despierta a demanda | **No** — permanente |
| **Render** (servicio web) | 750 horas-instancia/mes; se apaga tras ~15 min inactivo | **No** — persiste |
| **Supabase** (Postgres) | 500 MB; se pausa tras ~1 semana inactivo y los datos se conservan | **No** — se pausa |
| **Render** (Postgres) | 1 GB | **Sí** — se elimina 30 días después de su creación |
| **Railway** | Crédito de prueba de un solo uso | **Sí** — sin base de datos gratuita permanente |

Así que la receta gratuita de larga duración es **Neon (base de datos) + Render
(servicio web)**:

- **Neon** — regístrate en [neon.com](https://neon.com), crea un proyecto y copia
  la cadena de conexión (tiene el aspecto
  `postgresql://user:password@ep-xxx.aws.neon.tech/neondb?sslmode=require`).
- **Render** — *New → Blueprint*, elige el repositorio y pega la URL de Neon cuando
  te pida `DATABASE_URL`. El comando de arranque migra y luego inicia gunicorn, y
  HTTPS es automático. Para usar en su lugar una base de datos gestionada por
  Render, descomenta el bloque `databases:` en `render.yaml` — pero se elimina a los
  30 días.
- **Railway** — *New Project → Deploy from GitHub repo*, añade las variables del
  paso 2 en **Variables** y luego *Settings → Networking → Generate Domain*.
- **Cualquier otro sitio** — `pip install -r requirements.txt`, `flask db upgrade`,
  `gunicorn --bind 0.0.0.0:$PORT --workers 3 wsgi:app`. En un VPS, ejecuta gunicorn
  en `127.0.0.1:8000` detrás de nginx + TLS y define `TRUST_PROXY=1`; en Docker,
  parte de `python:3.12-slim` y ejecuta los mismos tres comandos.

### Lista de verificación para producción

- [ ] `SECRET_KEY` definida con un valor aleatorio (nunca la de por defecto).
- [ ] `SESSION_COOKIE_SECURE=1` y el sitio servido por HTTPS.
- [ ] `TRUST_PROXY=1` si un proxy termina el TLS.
- [ ] `DATABASE_URL` apunta a una base de datos persistente; `flask db upgrade` se ejecuta en el despliegue.
- [ ] El modo de depuración está desactivado (no ejecutes `python app.py` en producción).
- [ ] Copias de seguridad configuradas para la base de datos.

## Notas / fuera de alcance

- SQLite es la base de datos por defecto por comodidad; define `DATABASE_URL` para
  usar PostgreSQL o MySQL. Recuerda ejecutar `flask db upgrade` después.
- Define un `SECRET_KEY` fuerte y `SESSION_COOKIE_SECURE=1` en producción.
- El restablecimiento de contraseña, la verificación por correo, el
  filtrado/paginación de tareas y la gestión de cuentas más allá de ver al usuario
  actual están fuera de alcance a propósito (aparecen como añadidos candidatos en
  `USE-CASES.md`).
