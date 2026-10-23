from datetime import datetime
from uuid_extensions import uuid7
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import EmailAlreadyRegisteredException
from app.core.security import get_client
from app.models.clients import Clients
from app.models.enums import ClientTier
from app.schemas.client_schemas import AddClient, AddClientResponse


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

