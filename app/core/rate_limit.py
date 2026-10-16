from typing import Callable, Optional, Awaitable

from fastapi import Request
from fastapi_limiter.depends import RateLimiter


# ------------ IP ADDRESS RESOLVER -----------------
async def get_client_ip(request: Request) -> str:
    """Get the client's IP address from the request.

    If the request has an X-Forwarded-For header, use the first IP address in the list.
    Otherwise, return the client's host address.

    :param request: The request object from which to obtain the client's IP address.
    :return: The client's IP address as a string.
    """
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        # xff can contain multiple IPs, the first one is the client's IP
        return xff.split(",")[0].strip()
    return request.client.host


# ------------ RATE LIMITER KEY GENERATORS ----------------
async def default_rate_limit_key(request: Request):
    """Generate a rate limit key based on the request.

    If the request has a user attached, use the user's ID as the key.
    Otherwise, use the client's IP address as the key.

    :param request: The request object from which to obtain the rate limit key.
    :return: The rate limit key as a string.
    """
    user = getattr(request.state, "user", None)

    if user and getattr(user, "id", None):
        return f"user:{user.id}"

    # If the user is not authenticated, fallback to IP-based limiting
    return f"ip:{await get_client_ip(request)}"


# def user_rate_limit_key(request: Request):
#     user = getattr(request.state, "user", None)
#     if user and getattr(user, "id", None):
#         return f"user:{user.id}"
#     return None


def RateLimit(
    *,
    times: int,
    seconds: int,
    identifier: Optional[Callable[[Request], Awaitable[str]]] = None,
) -> RateLimiter:
    """Create a rate limiter based on the given parameters.

    If an identifier is given, it will be used as the key for the rate limiter.
    Otherwise, the default rate limit key function will be used, which is
    based on the client's IP address.

    :param times: The number of requests allowed within the given time period.
    :param seconds: The time period in seconds.
    :param identifier: An optional function or string that will be used as the
        key for the rate limiter.
    :return: A rate limiter object with the given parameters.
    """
    return RateLimiter(
        times=times, seconds=seconds, identifier=identifier or default_rate_limit_key
    )


# TODO: create an anon only rate limiter (anonymous users only)
# TODO: create an auth only rate limiter (authenticated users only)
