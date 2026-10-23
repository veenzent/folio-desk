import os
from datetime import datetime, timezone
from uuid import uuid4

os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault(
    "DEV_DB_URL", "postgresql+asyncpg://test:test@localhost/folio_desk_test"
)
os.environ.setdefault("DEV_REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("SECRET_KEY", "unit-test-secret-key")
os.environ.setdefault("ALGORITHM", "HS256")


def build_test_app():
    from fastapi import FastAPI

    from app.api.v1 import auth, client
    from app.core.error_handlers import register_error_handlers

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(client.router, prefix="/api/v1")
    return app


def client_response(**overrides):
    from app.models.enums import ClientTier

    now = datetime.now(timezone.utc)
    values = {
        "id": uuid4(),
        "name": "Example Client",
        "contact_email": "client@example.com",
        "tier": ClientTier.standard,
        "created_at": now,
        "updated_at": now,
    }
    values.update(overrides)
    return values
