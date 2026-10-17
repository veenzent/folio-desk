from datetime import datetime
from uuid_extensions import uuid7
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import EmailAlreadyRegisteredException, InvalidRoleException
from app.core.security import get_client, get_current_user
from app.models.clients import Clients
from app.models.enums import UserRole
from app.schemas.client_schemas import AddClient, AddClientResponse


async def create_new_client(client: AddClient, db: AsyncSession, token: str) -> AddClientResponse:
    """
    Create a new client in the database.

    Args:
        client (AddClient): The client data to create.
        db (AsyncSession): The database session.
        token (str): The authentication token of the user creating the client.

    Returns:
        AddClientResponse: The newly created client data.
    """
    # confirm if user is admin
    user = await get_current_user(db, token)

    if user.role != UserRole.admin:
        raise InvalidRoleException()

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
        tier=client.tier,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.add(new_client)
    await db.commit()
    await db.refresh(new_client)

    return AddClientResponse(new_client.model_dump())

