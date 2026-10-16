import re

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
DATABASE_URL = settings.effective_database_url

# Validate that we have a URL
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not set. "
        "Set DEV_DB_URL in .env for development or DATABASE_URL for production."
    )

# Convert to asyncpg scheme (Neon-compatible, following their recommended pattern)
# Handles both postgres:// and postgresql:// prefixes
DATABASE_URL = re.sub(r"^postgresql:", "postgresql+asyncpg:", DATABASE_URL)
DATABASE_URL = re.sub(r"^postgres:", "postgresql+asyncpg:", DATABASE_URL)

# Remove sslmode from URL query string (asyncpg handles SSL via connect_args instead)
DATABASE_URL = DATABASE_URL.split("?", 1)[0]

# Create the async engine
# For Neon (serverless), SSL is required — asyncpg will handle sslmode automatically
connect_args = {"server_settings": {"application_name": "FolioDesk"}}

is_neon = "neon.tech" in DATABASE_URL
if is_neon:
    connect_args["ssl"] = "require"  # Neon requires SSL
else:
    connect_args["ssl"] = False  # Local/dev DB does not use SSL

async_engine = create_async_engine(
    DATABASE_URL, echo=True, poolclass=NullPool, future=True, connect_args=connect_args
)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    future=True,
)
