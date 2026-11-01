# FolioDesk

FolioDesk is a backend API for a freelance developer or small agency that manages client requests, projects, and delivery status in one place. It is designed around the workflow of a solo operator who handles work for multiple clients while needing a clear queue, role-based access control, and a public-facing portfolio of selected projects.

This project is built with FastAPI and SQLAlchemy, with auth, rate limiting, and API conventions intended to support a client-facing request system and admin dashboard workflow.

## Why this project exists

The core problem FolioDesk addresses is fragmented client work:

- client requests arrive in different channels
- status and urgency are not tracked consistently
- there is no predictable queue for prioritizing maintenance work
- the admin has no central place to review requests and communicate progress
- portfolio work is stored separately and becomes stale

By centralizing this data, FolioDesk gives the admin a ranked work queue and gives clients a controlled, read-only view of their own projects and requests.

## Product scope

The intended workflow is:

1. Admin creates a client and issues an invite code.
2. Client registers and logs in.
3. Client submits a request against a project.
4. Admin reviews and prioritizes the queue.
5. Client receives status updates.
6. Selected projects are marked public and appear in a portfolio.

## Core entities

- User
- Client
- Project
- Request
- InviteCode
- Comment

## Roles

- Admin: freelancer / account owner with full access and managerial controls
- Client: registered user tied to one client record and limited to their own data
- Public: unauthenticated user who can view public portfolio content only

## Architecture and stack

- Python 3.13+
- FastAPI
- SQLAlchemy + async database engine
- PostgreSQL-compatible database (including Neon/Postgres setups)
- Redis for request rate limiting
- JWT for authentication
- Pydantic validation and schema models
- pytest test runner with Python `unittest` cases, FastAPI `TestClient`, and mocked async database sessions

## Repository structure

```text
.
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── tests/
├── .env
├── ERD.dbml
├── folio-desk-API-Spec.yaml
├── one-pager.md
├── one-pager-wk3.md
├── pyproject.toml
├── uv.lock
├── README.md
└── ...
```

## Getting started

### 1. Clone the repo

```bash
git clone https://github.com/veenzent/folio-desk.git
cd folio-desk
```

### 2. Install dependencies

This project uses `uv` for dependency management and is configured in `pyproject.toml`.

```bash
uv sync
```

### 3. Configure environment variables

Copy [`.env.sample`](./.env.sample) to `.env` and replace the example values with your local settings. At a minimum, the app expects values similar to:

```env
ENVIRONMENT=development
APP_NAME="Folio Desk"
SECRET_KEY=replace_with_a_long_random_secret
ALGORITHM=HS256
DATABASE_URL=postgresql://<user>:<password>@<host>:5432/<database>
DEV_DB_URL=postgresql://<user>:<password>@localhost:5432/folio_desk
REDIS_URL=redis://localhost:6379/1
DEV_REDIS_URL=redis://localhost:6379/1
DEV_ORIGINS=http://localhost:3000
ORIGINS=https://your-frontend.example
```

Notes:
- In development, `DEV_DB_URL` and `DEV_REDIS_URL` are selected. In production, configure `DATABASE_URL`, `REDIS_URL`, and `ORIGINS` instead.
- Database URLs may use `postgresql://` or `postgres://`; the application adapts them to the async PostgreSQL driver. The configured database must exist and be reachable.
- Configure explicit allowed origins in production. Development CORS defaults are permissive if `DEV_ORIGINS` is omitted.
- `SECRET_KEY` must be a strong private value. Other settings, including token expiration and email-provider settings, are defined in `app/core/config.py`.
- The app checks database connectivity at startup and creates missing tables from SQLAlchemy metadata. This is convenient for development; use a deliberate migration process for production schema changes.
- Redis is initialized for the limiter integration at startup. The custom route limiter currently keeps its counters in process memory, so limits are not shared across multiple workers or instances.

## Running the app

Start the FastAPI application with:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open:

- API docs: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

## API conventions

The API is built around a few deliberate design rules:

- routes live under `/api/v1`
- authentication is token-based using JWT
- clients are only allowed to access their own data
- validation errors return HTTP 400
- access control issues are handled with clear 401/403/404 responses
- rate limiting is enforced on authentication and sensitive endpoints

The standalone [`folio-desk-API-Spec.yaml`](./folio-desk-API-Spec.yaml) describes the intended API contract. It currently covers more endpoints than are wired into `app/main.py`; the running application currently includes Auth, Client, and Invites routers. Confirm an endpoint is implemented before relying on its contract.

## Current project status

This repository is in an active backend development phase. The codebase includes the FastAPI foundation, auth scaffolding, configuration, and the project structure needed for the FolioDesk domain model, but the platform is still evolving toward the complete feature set described in the product docs.

## Supporting documents

The project includes several planning and specification documents:

- `one-pager.md` — summary of the product concept and goals
- `one-pager-wk3.md` — Week 3 testing, documentation, security, and delivery status, including known gaps
- `folio-desk-API-Spec.yaml` — API contract and endpoint design
- `ERD.dbml` — entity relationship model
- `FolioDesk Product Requirements Document.docx` — formal product requirements

## Development notes

Because this is a service-first project, the most important patterns to preserve are:

- enforce tenant/client isolation at the service and database query layer
- keep queue priority logic explicit and explainable
- validate every request before business logic executes
- treat invite codes as one-time, expiring registration tokens
- keep the public portfolio restricted to explicitly approved projects

## Testing

The test runner is **pytest**. Test cases use Python's built-in `unittest` and `unittest.mock`, with FastAPI's `TestClient` for route tests. The suite currently covers selected auth and client service logic and routes.

Install dependencies (including pytest) with `uv sync`, then run all tests from the repository root with one command:

```bash
uv run pytest
```

You can run one test module or select a test by name:

```bash
uv run pytest tests/test_auth.py
uv run pytest tests/test_client.py -k pagination
```

The current suite has **20 passing tests**. Tests use mocked services and async database sessions; they do not yet exercise a separate or in-memory database, full client-to-client isolation, or all documented endpoints and failure cases. Coverage instrumentation is not configured, so no coverage percentage is claimed. Expand the suite as routes are implemented, especially with database-backed integration tests for ownership boundaries and 400/401/403/404 behavior.

The Week 3 status and detailed tested/not-tested list are in [`one-pager-wk3.md`](./one-pager-wk3.md).

## Deployment status

This repository currently provides a local setup and run guide, but no verified hosted deployment or checked-in Docker configuration. See the Week 3 status page for outstanding delivery work.

## License

This project does not currently declare a formal license in the repository.

## Contributing

This project is intended to evolve with a clear product boundary. If you are contributing:

- preserve the role-based access rules
- keep business logic aligned with the product spec
- add tests for security-sensitive changes
- avoid widening scope into monitoring, payments, or frontend features unless the requirements explicitly include them
