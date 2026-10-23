import secrets

from app.core.security import get_hasher
from app.services.client_services import get_client, get_client_by_id


def generate_invitation_code() -> str:
    """Generate a secure, URL-friendly invitation code."""
    return secrets.token_urlsafe(32)


def hash_invitation_code(invitation_code: str) -> str:
    """Hash the invitation code to make it more secure."""
    hashed_code = get_hasher(invitation_code)

    return hashed_code


async def create_invitation(client_id: str, db):
    # generate invitation code
    invitation_code = generate_invitation_code()

    # hash invitation code
    hashed_invitation_code = hash_invitation_code(invitation_code)

    # get client by id and access their email
    client = await get_client_by_id(db, client_id)

    # send email to client

    return hashed_invitation_code