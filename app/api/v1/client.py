from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import RateLimit
from app.core.security import get_db, get_current_admin
from app.schemas.client_schemas import AddClient, AddClientResponse, ClientsResponse
from app.models.clients import ClientTier
from app.services.client_services import create_new_client, get_all_clients, delete_client

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
    deprecated=True,
    summary="Get a client by ID",
    dependencies=[Depends(RateLimit(times=10, seconds=60)), Depends(get_current_admin)],
    response_model=ClientsResponse,
)
async def get_client_by_id(id: str, db: AsyncSession = Depends(get_db)) -> ClientsResponse:
    """
    Admin only route to get a client by ID.
    """
    clients: list[ClientsResponse] = await get_all_clients(db, skip=0, limit=1000)
    client = next((client for client in clients if client.id == id), None)

    if not client:
        return {"message": f"Client with ID {id} not found."}

    return client


@router.patch(
    "/{id}",
    deprecated=True,
    summary="Update a client",
    dependencies=[Depends(RateLimit(times=10, seconds=60)), Depends(get_current_admin)],
)
async def update_client_by_id(id: str, client: AddClient, db: AsyncSession = Depends(get_db)):
    """
    Admin only route to update a client.
    """
    clients: list[ClientsResponse] = await get_all_clients(db, skip=0, limit=1000)
    existing_client = next((c for c in clients if c.id == id), None)

    if not existing_client:
        return {"message": f"Client with ID {id} not found."}

    # Update the existing client with new data
    updated_client_data = client.dict(exclude_unset=True)
    for key, value in updated_client_data.items():
        setattr(existing_client, key, value)

    # Here you would typically save the updated client back to the database
    # For example: await save_updated_client(existing_client, db)

    return {"message": f"Client with ID {id} has been updated.", "client": existing_client}


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


