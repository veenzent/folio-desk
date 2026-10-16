from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import RateLimit
from app.core.security import (
    authenticate_user,
    create_access_token,
    get_db,
    settings,
    get_current_user,
)
from app.schemas.auth_schemas import RegisterRequest, RegisterRequestResponse, Token
from app.services.auth_services import create_new_user

router = APIRouter(prefix="/auth")


@router.post(
    "/register",
    summary="Register a client user with an invite code",
    dependencies=[Depends(RateLimit(times=10, seconds=60))],
    response_model=RegisterRequestResponse,
)
async def register_user(
    client_user: RegisterRequest, db: AsyncSession = Depends(get_db)
) -> RegisterRequestResponse:
    """
    Consumes the invite code and links it to the new user in one transaction. No token is returned; the client logs in next.
    """
    new_user: RegisterRequestResponse = await create_new_user()

    return new_user


@router.post("/login", summary="Log in with email and password")
async def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
):
    """
    Log in with email and password. Returns a token.
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email_address}, expires_delta=access_token_expires
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        refresh_token="sample_refresh_token",  # TODO: Add refresh token
    )


@router.get("/me", summary="Get current user")
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(get_current_user),
):
    """
    Get the current logged-in user based on the provided token.
    """
    user = await authenticate_user(db, token=token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user