from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import RateLimit
from app.core.security import get_db, get_current_admin
from app.schemas.client_schemas import AddClient, AddClientResponse
from app.models.clients import ClientTier
from app.services.client_services import create_new_client

router = APIRouter(prefix="/clients")


@router.post(
    "",
    summary="Create a client",
    dependencies=[Depends(RateLimit(times=10, seconds=60)), Depends(get_current_admin)],
    response_model=AddClientResponse,
)
async def create_client(
    client: AddClient,
    tier: ClientTier,
    db: AsyncSession = Depends(get_db),
) -> AddClientResponse:
    """
    Admin only route to add clients.
    """
    new_client: AddClientResponse = await create_new_client(client, tier, db)

    return new_client
