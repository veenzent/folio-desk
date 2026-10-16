import asyncio
import logging
from typing import AsyncGenerator

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.db.base import AsyncSessionLocal, Base

log = logging.getLogger(__name__)


async def ping_db(async_engine: AsyncEngine) -> bool:
    """Ping the database to check connectivity."""
    try:
        async with async_engine.connect() as conn:
            res = await conn.execute(text("select 'hello world'"))
            val = res.scalar()
            log.info("Ping DB response: %s", val)
        return bool(val is not None)
    except Exception as e:
        log.warning("Database connection error: %s", e, exc_info=True)
        return False


async def wait_for_db(
    async_engine: AsyncEngine, retries: int = 5, delay: float = 2.0
) -> bool:
    for attempt in range(1, retries + 1):
        ok = await ping_db(async_engine)
        if ok:
            log.info("Database is ready (attempt %d/%d)", attempt, retries)
            return True
        log.warning(
            "Database not ready (attempt %d/%d), waiting %.1fs...",
            attempt,
            retries,
            delay,
        )
        await asyncio.sleep(delay)
    log.error("Database not reachable after %d attempts", retries)
    return False


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables(async_engine: AsyncEngine):
    async with async_engine.begin() as conn:
        # create all missing tables (runs in sync context)
        await conn.run_sync(Base.metadata.create_all)

        # run inspection in sync context as well
        def _get_table_names(sync_conn):
            insp = inspect(sync_conn)
            return insp.get_table_names()

        tables = await conn.run_sync(_get_table_names)
        log.info("Existing tables after create_all: %s", tables)

        return tables
