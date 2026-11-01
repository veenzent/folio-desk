# FolioDesk — Week 3: Quality and Delivery

## Goal

Deliver a tested, documented, and basically secured API with a reproducible local
setup. This page records the current repository evidence and the remaining work;
it does not claim that planned API features or a production deployment are already
complete.

## Delivery status

| Deliverable | Current status | Evidence / next step |
|---|---|---|
| Test suite and coverage note | **Implemented, partial coverage** | `uv run pytest` passes all 20 tests. Tests cover selected auth and client service logic and HTTP routes; the coverage note below lists gaps. |
| API documentation | **Contract documented** | [`folio-desk-API-Spec.yaml`](./folio-desk-API-Spec.yaml) is an OpenAPI 3.0.3 specification with endpoint descriptions, auth requirements, examples, and response cases. FastAPI also serves Swagger UI at `/docs` and ReDoc at `/redoc` when the app is running. |
| Setup guide | **Available for local development** | [`README.md`](./README.md) documents dependency installation, environment configuration, startup, and local API URLs. |
| Security basics | **Partial; production review required** | Settings support environment-based configuration, request models validate input, and auth/sensitive routes have rate-limit dependencies. See the security notes below before deployment. |
| Performance basics | **Partial** | Client listing supports bounded pagination, and selected model fields have indexes. Confirm pagination and indexes for every implemented list/filter query as those API areas are completed. |
| Deployment | **Local run guide only** | No live deployment or Docker setup is included in the repository. Use the README local setup; deployment remains outstanding. |

## Task 3.1 — Testing

### Run the tests

From the repository root, install project dependencies with `uv sync` if needed,
then run:

```bash
uv run pytest
```

Latest checked result: **20 passed**. Pytest also reports three dependency or
deprecation warnings; they do not fail the suite.

### Coverage note

**Tested**

- Password requirement validation and selected admin-registration success,
  duplicate-user, and database-integrity-error behavior.
- Client creation, duplicate-email handling, record mapping, pagination query
  parameters, and delete success/not-found behavior.
- HTTP route behavior for login success and invalid credentials, current-user
  retrieval, registration, client creation/listing/deletion, and an admin-role
  rejection.

**Not yet covered, or not covered end to end**

- Tests use mocked services and `AsyncMock` database sessions. Although test
  database settings are provided in the test support module, the suite does not
  exercise persistence against a separate or in-memory database.
- Cross-client ownership/isolation across the full API, and end-to-end invite,
  project, request, comment, dashboard, and portfolio workflows.
- A comprehensive endpoint-level matrix for 400, 401, 403, and 404 responses.
  Current tests include invalid-login 401, role-rejection 403, and a service
  not-found 404; they do not establish that every relevant endpoint handles
  these cases correctly.
- Measured line or branch coverage. No coverage percentage is claimed because
  coverage instrumentation has not been run.

## Task 3.2 — Documentation, security, and delivery

### API documentation

The OpenAPI file documents the planned API contract, including auth, request
examples, and common error responses. The running FastAPI app exposes interactive
documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

The contract is broader than the routers currently wired in `app/main.py`
(Auth, Client, and Invites). Verify each documented endpoint against the running
implementation before treating the full specification as a delivered API.

### Setup and run guide

Follow [`README.md`](./README.md) to install dependencies, configure `.env`, and
start the local server. The documented launch command is:

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The README provides local API docs and health-check URLs. There is no checked-in
Docker configuration or verified hosted endpoint at this time.

### Security notes

- Supply secrets and credentials through environment variables; replace all
  development/example values with strong deployment-specific values. The
  settings module includes defaults, so do not rely on those defaults in
  production.
- Configure the production CORS origin allowlist deliberately. Development
  origins currently default to `*`; do not use that development setting as a
  production policy.
- Request schemas provide input validation. Review endpoint-specific
  sanitization and authorization as additional routes are implemented.
- Rate limiting is attached to auth and selected sensitive routes. The custom
  limiter stores request buckets in application memory, so limits are not shared
  across multiple workers or instances. Use a shared/distributed limiter for a
  multi-instance deployment.
- The API contract documents bearer authentication and the intended 400/401/403/
  404 error conventions. Keep implementation and contract behavior aligned.

### Performance notes

- The client list endpoint accepts `page_size` and `page_number` and caps the
  page size at 100.
- Selected model fields are indexed. Review query filters and ordering for each
  completed endpoint and add indexes only where supported by actual query
  patterns.
- Pagination is not yet demonstrated across every documented list endpoint.

## Remaining Week 3 actions

1. Add database-backed integration coverage using an isolated test database or
   an in-memory database, and cover ownership boundaries and endpoint failure
   cases.
2. Measure coverage and retain an honest tested/not-tested note as the suite
   expands.
3. Reconcile the OpenAPI contract with implemented routes and verify examples,
   authentication, and error responses against the app.
4. Require production environment secrets and an explicit CORS allowlist; move
   rate limiting to shared storage before scaling beyond one process.
5. Choose a deployment target or add a Docker/local deployment guide, then
   verify a deployed or reproducible run path.
