from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import RateLimit
from app.core.security import get_db, get_current_admin
from app.schemas.client_schemas import AddClient, AddClientResponse, ClientsResponse, UpdateClient
from app.models.clients import ClientTier
from app.services.client_services import (
    create_new_client,
    get_client_by_id as get_client,
    get_all_clients,
    delete_client,
    update_client_data
)


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


@router.get(
    "",
    summary="Get all clients",
    dependencies=[Depends(RateLimit(times=10, seconds=60)), Depends(get_current_admin)],
    response_model=list[ClientsResponse],
)
async def get_clients(
    page_size: int = Query(10, ge=1, le=100, description="Number of clients to return per page"),
    page_number: int = Query(1, ge=1, description="Page number to retrieve"),
    db: AsyncSession = Depends(get_db)
) -> list[ClientsResponse]:
    """
    Admin only route to get all clients.
    """
    skip = (page_number - 1) * page_size
    clients: list[ClientsResponse] = await get_all_clients(db, skip=skip, limit=page_size)

    return clients


@router.get(
    "/{id}",
    summary="Get a client by ID",
    dependencies=[Depends(RateLimit(times=10, seconds=60)), Depends(get_current_admin)],
    response_model=ClientsResponse,
)
async def get_client_by_id(id: str, db: AsyncSession = Depends(get_db)) -> ClientsResponse:
    """
    Admin only route to get a client by ID.
    """
    client: ClientsResponse | None = await get_client(db, id)

    if not client:
        return {"message": f"Client with ID {id} not found."}

    return client


@router.patch(
    "/{id}",
    summary="Update a client",
    dependencies=[Depends(RateLimit(times=10, seconds=60)), Depends(get_current_admin)],
)
async def update_client_by_id(
    id: str,
    tier: ClientTier | None = None,
    client: UpdateClient | None = None,
    db: AsyncSession = Depends(get_db)) -> ClientsResponse | dict:
    """
    Admin only route to update a client.
    """
    updated: ClientsResponse = await update_client_data(id, tier, client, db)

    return updated


@router.delete(
    "/{id}",
    summary="Delete a client",
    dependencies=[Depends(RateLimit(times=10, seconds=60)), Depends(get_current_admin)],
)
async def delete_client_by_id(id: str, db: AsyncSession = Depends(get_db)):
    """
    Admin only route to delete a client.
    """
    await delete_client(id, db)
    return {"message": f"Client with ID {id} has been deleted."}


