from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
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
    # TODO: implement the logic to create a new client in the database

    # This is a placeholder implementation. Replace it with your actual database logic.
    new_client = AddClientResponse(
        name=client.name,
        contact_email=client.contact_email,
        tier=client.tier,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    return new_client