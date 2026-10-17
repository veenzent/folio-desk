from datetime import datetime, timedelta, timezone
from typing import Annotated, AsyncGenerator, Literal
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_async_db
from app.models.users import Users
from app.models.clients import Clients
from app.schemas.client_schemas import AddClientResponse
from app.schemas.users import TokenData, UserExternalResponse, UserInternalResponse

settings = get_settings()
hasher = PasswordHash.recommended()
# TODO: Add a different hash algorithm for refresh token hashing
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


# ----------------------- Password and Refresh Token Hashing ----------------------- #
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a hashed password.

    Args:
        plain_password (str): The plaintext password to verify.
        hashed_password (str): The hashed password to verify against.

    Returns:
        bool: True if the plaintext password matches the hashed password.
    """
    return hasher.verify(plain_password, hashed_password)


def get_hasher(password: str) -> str:
    """
    Return a hashed version of the given plaintext password.

    Args:
        password (str): The plaintext password to hash.

    Returns:
        str: The hashed password.
    """
    return hasher.hash(password)


def get_refresh_token_hash(refresh_token: str) -> str:
    """
    Return a hashed version of the given plaintext refresh token.

    Args:
        refresh_token (str): The plaintext refresh token to hash.

    Returns:
        str: The hashed refresh token.
    """
    return hasher.hash(refresh_token)


# ----------------------- User Retrieval and Authentication ----------------------- #
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency wrapper that yields AsyncSession from `get_async_db`.

    Use `Depends(get_db)` in route handlers and other dependencies.
    """
    async for session in get_async_db():
        yield session


async def get_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    email_address: EmailStr
) -> UserInternalResponse | None:
    """
    Retrieve a user object from the database by email address.

    Args:
        db (Annotated[AsyncSession, Depends(get_db)]): The async database session.
        email_address (EmailStr): The email address of the user to retrieve.

    Returns:
        UserInternalResponse | None: The user object if found, otherwise None.
    """
    result = await db.execute(
        select(Users).where(Users.email == email_address)
    )
    user_obj = result.scalar_one_or_none()
    if not user_obj:
        return None

    return UserInternalResponse(
        id=getattr(user_obj, "id", None),
        client_id=getattr(user_obj, "client_id", ""),
        email=getattr(user_obj, "email", ""),
        password_hash=getattr(user_obj, "password_hash", ""),
        role=getattr(user_obj, "role", ""),
        is_active=getattr(user_obj, "is_active", False),
        created_at=getattr(user_obj, "created_at", ""),
    )


async def get_client(
    db: Annotated[AsyncSession, Depends(get_db)],
    email_address: EmailStr
) -> AddClientResponse | None:
    """
    Retrieve a client object from the database by email address.

    Args:
        db (Annotated[AsyncSession, Depends(get_db)]): The async database session.
        email_address (EmailStr): The email address of the client to retrieve.

    Returns:
        UserInternalResponse | None: The client object if found, otherwise None.
    """
    result = await db.execute(
        select(Clients).where(Clients.contact_email == email_address)
    )
    client_obj = result.scalar_one_or_none()
    if not client_obj:
        return None

    return AddClientResponse(
        id=getattr(client_obj, "id", None),
        name=getattr(client_obj, "name", ""),
        contact_email=getattr(client_obj, "contact_email", ""),
        tier=getattr(client_obj, "tier", ""),
        created_at=getattr(client_obj, "created_at", ""),
        updated_at=getattr(client_obj, "updated_at", ""),
    )


async def get_user_by_phone(
    db: Annotated[AsyncSession, Depends(get_db)], phone_number: str
) -> UserInternalResponse | None:
    """
    Retrieve a user object from the database by phone number.

    Args:
        db (Annotated[AsyncSession, Depends(get_db)]): The async database session.
        phone_number (str): The phone number of the user to retrieve.

    Returns:
        UserInternalResponse | None: The user object if found, otherwise None.
    """
    result = await db.execute(
        select(Users).where(Users.phone_number == phone_number)
    )
    user_obj = result.scalar_one_or_none()
    if not user_obj:
        return None

    return UserInternalResponse(
        id=getattr(user_obj, "id", None),
        email_address=getattr(user_obj, "email_address", ""),
        phone_number=getattr(user_obj, "phone_number", ""),
        password_hash=getattr(user_obj, "password_hash", ""),
        is_active=getattr(user_obj, "is_active", False),
    )


async def get_user_by_id(
    db: Annotated[AsyncSession, Depends(get_db)], user_id: UUID
) -> UserInternalResponse | None:
    """
    Retrieve a user object from the database by user ID.

    Args:
        user_id (uuid): The user ID of the user to retrieve.
        db (Annotated[AsyncSession, Depends(get_db)]): The async database session.

    Returns:
        UserInternalResponse | None: The user object if found, otherwise None.
    """
    result = await db.execute(select(Users).where(Users.id == user_id))
    user_obj = result.scalar_one_or_none()
    if not user_obj:
        return None

    return UserInternalResponse(
        id=getattr(user_obj, "id", None),
        email_address=getattr(user_obj, "email_address", ""),
        phone_number=getattr(user_obj, "phone_number", ""),
        password_hash=getattr(user_obj, "password_hash", ""),
        is_active=getattr(user_obj, "is_active", False),
    )


async def authenticate_user(
    db: Annotated[AsyncSession, Depends(get_db)], username: str, password: str
) -> UserExternalResponse | Literal[False]:
    user = await get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return UserExternalResponse(**user.model_dump())


# ----------------------- JWT Token Creation and Verification ----------------------- #
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    # sample to_encode = {"sub": user.email_address, "id": str(user.id)}
    to_encode = data.copy()
    if not expires_delta:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    expire = datetime.now(timezone.utc) + expires_delta

    to_encode.update({"exp": expire})
    # encoded_jwt
    access_token = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )

    return access_token


def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if not expires_delta:
        expires_delta = timedelta(days=settings.refresh_token_expire_days)

    expire = datetime.now(timezone.utc) + expires_delta

    to_encode.update({"exp": expire})
    refresh_token = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )

    return refresh_token


async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> UserInternalResponse:
    """
    Retrieves the currently authenticated user from the provided token.

    Args:
        request (Request): The incoming request.
        db (Annotated[AsyncSession, Depends(get_db)]): The async database session.
        token (Annotated[str, Depends(oauth2_scheme)]): The provided access token.

    Returns:
        UserInternalResponse: The currently authenticated user.

    Raises:
        HTTPException: If the provided token is invalid or cannot be decoded.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload: dict = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        email_address = payload.get("sub")
        if email_address is None:
            raise credentials_exception

        token_data = TokenData(email_address=email_address)
    except InvalidTokenError:
        raise credentials_exception

    # `db` should already be an AsyncSession provided by Depends(get_db)
    user = await get_user(db, email_address=token_data.email_address)
    if user is None:
        raise credentials_exception

    # Attach user to request state for downstream access
    request.state.user = user

    return user
