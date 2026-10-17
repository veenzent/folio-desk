from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import RateLimit
from app.core.security import get_db, get_current_user
from app.schemas.client_schemas import AddClient, AddClientResponse
from app.services.client_services import create_new_client

router = APIRouter(prefix="/clients")


@router.post(
    "",
    summary="Create a client",
    dependencies=[Depends(RateLimit(times=10, seconds=60))],
    response_model=AddClientResponse,
)
async def create_client(
    client: AddClient,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(get_current_user),
) -> AddClientResponse:
    """
    Admin only.
    """
    new_client: AddClientResponse = await create_new_client(client, db, token)

    return new_client
