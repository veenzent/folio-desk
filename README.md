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
- pytest-ready service structure for auth and security workflows

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

### 2. Create a virtual environment and install dependencies

This project uses `uv` for dependency management and is configured in `pyproject.toml`.

```bash
uv sync
```

If you prefer a standard Python setup:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

### 3. Configure environment variables

Create or update a `.env` file in the project root with the required app settings. At a minimum, the app expects values similar to:

```env
ENVIRONMENT=development
APP_NAME="Folio Desk"
SECRET_KEY=your_secret_key
ALGORITHM=HS256
DATABASE_URL=postgresql://user:password@host:5432/dbname
DEV_DB_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://localhost:6379/1
DEV_REDIS_URL=redis://localhost:6379/1
```

Notes:
- `ENVIRONMENT` switches between development and production settings.
- `DATABASE_URL` is used in production; `DEV_DB_URL` can be used during development.
- Redis is used for the rate-limiting layer.

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

## Current project status

This repository is in an active backend development phase. The codebase includes the FastAPI foundation, auth scaffolding, configuration, and the project structure needed for the FolioDesk domain model, but the platform is still evolving toward the complete feature set described in the product docs.

## Supporting documents

The project includes several planning and specification documents:

- `one-pager.md` — summary of the product concept and goals
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

The application is set up to support test coverage for auth, security, and client isolation. The repo currently contains the initial test scaffold and should be expanded as features are implemented.

```bash
pytest
```

## License

This project does not currently declare a formal license in the repository. If you intend to distribute or publish it, add a license file and update this section accordingly.

## Contributing

This project is intended to evolve with a clear product boundary. If you are contributing:

- preserve the role-based access rules
- keep business logic aligned with the product spec
- add tests for security-sensitive changes
- avoid widening scope into monitoring, payments, or frontend features unless the requirements explicitly include them
