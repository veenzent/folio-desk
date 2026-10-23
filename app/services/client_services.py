from datetime import datetime
from uuid_extensions import uuid7

from pydantic import EmailStr
from typing import Annotated
from fastapi import Depends, HTTPException, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.exceptions import EmailAlreadyRegisteredException
from app.core.security import get_db
from app.models.clients import Clients
from app.models.enums import ClientTier
from app.schemas.client_schemas import AddClient, AddClientResponse, ClientsResponse


async def create_new_client(client: AddClient, tier: ClientTier, db: AsyncSession) -> AddClientResponse:
    """
    Create a new client in the database.

    Args:
        client (AddClient): The client data to create.
        tier (ClientTier): The tier of the new client.
        db (AsyncSession): The database session.

    Returns:
        AddClientResponse: The newly created client data.
    """
    # Check if the contact email is already registered.
    # TODO: I would rely on DB's unique constraint to perform duplicate checks for better perfomance at scale 📝
    if await get_client(
            db, client.contact_email.lower()
        ): 
            raise EmailAlreadyRegisteredException()

    # add client to database
    new_client = Clients(
        id=uuid7(),
        name=client.name,
        contact_email=client.contact_email,
        tier=tier,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.add(new_client)
    await db.commit()
    await db.refresh(new_client)

    return AddClientResponse(
        id=new_client.id,
        name=new_client.name,
        contact_email=new_client.contact_email,
        tier=new_client.tier,
        created_at=new_client.created_at,
        updated_at=new_client.updated_at
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
        AddClientResponse | None: The client object if found, otherwise None.
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


async def get_client_by_id(
    db: Annotated[AsyncSession, Depends(get_db)],
    id: str
) -> AddClientResponse | None:
    """
    Retrieve a client object from the database by ID.

    Args:
        db (Annotated[AsyncSession, Depends(get_db)]): The async database session.
        id (str): The ID of the client to retrieve.

    Returns:
        AddClientResponse | None: The client object if found, otherwise None.
    """
    result = await db.execute(
        select(Clients).where(Clients.id == id)
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


async def get_all_clients(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 10,
) -> list[ClientsResponse] | None:
    statement = (
        select(Clients)
        .order_by(Clients.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(statement)
    clients = result.scalars().all()

    return [
        ClientsResponse(
            id=client.id,
            name=client.name,
            contact_email=client.contact_email,
            tier=client.tier,
            created_at=client.created_at,
            updated_at=client.updated_at
        )
        for client in clients
    ]


async def delete_client(
    id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """
    Delete a client from the database.

    Args:
        id (str): The ID of the client to delete.
        db (AsyncSession): The database session.
    """
    statement = delete(Clients).where(Clients.id == id)
    result = await db.execute(statement)

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    await db.commit()