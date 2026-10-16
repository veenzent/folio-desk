import json
import logging
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter

from app.api.v1 import auth, client
from app.core.config import get_settings
from app.core.error_handlers import register_error_handlers
from app.core.rate_limit import RateLimit
from app.db.base import async_engine
from app.db.session import create_tables, ping_db, wait_for_db


class SimpleJSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record into a JSON string.

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: The formatted log record as a JSON string.
        """
        payload = {
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "timestamp": self.formatTime(record, self.datefmt),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


log = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(SimpleJSONFormatter())
log.setLevel(logging.INFO)
log.addHandler(handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run startup tasks

    # initialize rate limiter
    redis_conn = redis.from_url(
        settings.effective_redis_url, encoding="utf-8", decode_responses=True
    )
    try:
        await FastAPILimiter.init(redis_conn)
        log.info("Rate limiter initialized")
    except Exception:
        log.warning("Rate limiter disabled (Redis not reachable)")

    # check db connection
    db_ping_status_ok = await wait_for_db(async_engine, retries=2)
    if not db_ping_status_ok:
        log.error("Database not reachable at startup; skipping table creation")
        yield
        return

    # create tables if not existing
    created = await create_tables(async_engine)
    if created:
        log.info("Startup: created tables: %s", created)
    else:
        log.info("Startup: no tables needed creation")

    yield
    # shutdown tasks go after yield


app = FastAPI(
    title="FolioDesk API",
    description="""
    FolioDesk lets a freelance developer manage the client systems he maintains.
    Clients log in to raise change requests on their own projects. The admin (the freelancer)
    sees one ranked queue of work and publishes selected projects as a public portfolio.

    **Roles:** Public (no token), Client, Admin

    **Conventions**
    - All routes sit under `/api/v1`. Ids are UUIDs. Timestamps are ISO 8601 in UTC.
    - A client who asks for another client's resource gets **404**, not 403, so its existence is not revealed.
      403 is used when the role itself may not call the endpoint.
    - Validation errors return **400** (not FastAPI's default 422).
    - Every error uses the same shape: `{ "error": { "code", "message", "details" } }`.
    - Login and register are limited to 10 calls per minute per IP (429).

    **Order of checks:** rate limit (429), authenticate (401), role (403), validate input (400),
    load resource scoped to the caller's client (404), business rules (409), perform the change.
    """,
    version="0.1.0",
    # docs_url="/",
    contact={
        "name": "FolioDesk Services",
        "email": "service.foliodesk@gmail.com",
    },
    lifespan=lifespan,
)


settings = get_settings()

# Choose allowed origins based on the environment (development vs production)
origins = settings.allowed_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)


# app.include_router(auth.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1", tags=["Auth"])
app.include_router(client.router, prefix="/api/v1", tags=["Client"])

# health check
@app.get(
    "/health", tags=["Health Check"], dependencies=[Depends(RateLimit(times=10, seconds=60))]
)
async def health_check(request: Request):
    # db_ping_status = await wait_for_db(async_engine, retries=2)
    db_ping_status = await ping_db(async_engine)
    print("Database connection status: ", db_ping_status)
    return {"status": "OK"}

