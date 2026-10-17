import time
from typing import Awaitable, Callable, Optional

from fastapi import HTTPException, Request


# ------------ IP ADDRESS RESOLVER -----------------
async def get_client_ip(request: Request) -> str:
    """Get the client's IP address from the request."""
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return "unknown"


# ------------ RATE LIMITER KEY GENERATORS ----------------
async def default_rate_limit_key(request: Request):
    """Generate a rate limit key based on the request."""
    user = getattr(request.state, "user", None)
    if user and getattr(user, "id", None):
        return f"user:{user.id}"
    return f"ip:{await get_client_ip(request)}"


def RateLimit(
    *,
    times: int,
    seconds: int,
    identifier: Optional[Callable[[Request], Awaitable[str]]] = None,
):
    """Return a dependency that enforces a simple sliding-window limiter.

    We intentionally avoid fastapi-limiter's `RateLimiter` dependency because its
    `__call__` inspects `route.path` and crashes for included routers in newer
    FastAPI versions.
    """
    key_func = identifier or default_rate_limit_key

    async def rate_limit_dependency(request: Request):
        key = await key_func(request)
        now = time.monotonic()
        state = getattr(request.app.state, "rate_limit_store", None)
        if state is None:
            request.app.state.rate_limit_store = {}
            state = request.app.state.rate_limit_store

        bucket = state.setdefault(key, [])
        bucket[:] = [ts for ts in bucket if now - ts < seconds]

        if len(bucket) >= times:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        bucket.append(now)
        return True

    return rate_limit_dependency


# TODO: create an anon only rate limiter (anonymous users only)
# TODO: create an auth only rate limiter (authenticated users only)
