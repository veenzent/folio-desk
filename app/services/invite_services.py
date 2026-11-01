from datetime import datetime, timezone, timedelta
from http.client import HTTPException
import secrets
import uuid

from fastapi import Depends
from typing import Annotated

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_hasher, get_db
from app.schemas.invite_schemas import AddInviteData, InviteResponse
from app.schemas.invite_schemas import InviteResponse
from app.models.invite_codes import InviteCodes
from app.services.client_services import get_client, get_client_by_id


def generate_invitation_code() -> str:
    """Generate a secure, URL-friendly invitation code."""
    return secrets.token_urlsafe(32)


def hash_invitation_code(invitation_code: str) -> str:
    """Hash the invitation code to make it more secure."""
    hashed_code = get_hasher(invitation_code)

    return hashed_code


async def create_invitation(client_id: str, db) -> InviteResponse:
    # generate invitation code
    invitation_code = generate_invitation_code()

    # hash invitation code
    hashed_invitation_code = hash_invitation_code(invitation_code)

    # get client by id and access their email
    client = await get_client_by_id(db, client_id)

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    #TODO: send email to client

    # add invite data to db
    invite_data = InviteCodes(
        id=uuid.uuid4(),
        client_id=client.id,
        code_hash=hashed_invitation_code,
        expires_at=timedelta(days=7) + datetime.now(timezone.utc),
        used_at=None,
        revoked_at=None,
        created_at=datetime.now(timezone.utc),
    )

    db.add(invite_data)
    await db.commit()
    await db.refresh(invite_data)

    # return hashed_invitation_code
    return InviteResponse(
        id=invite_data.id,
        client_id=client_id,
        invite_code=invitation_code,
        created_at=invite_data.created_at,
        expires_at=invite_data.expires_at,
    )


async def get_all_invites(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 10,
) -> list | list[InviteResponse]:
    statement = (
        select(InviteCodes)
        .order_by(InviteCodes.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(statement)
    invites = result.scalars().all()

    if not invites:
        return []

    return [
        InviteResponse(
            id=str(invite.id),
            client_id=str(invite.client_id),
            invite_code=invite.code_hash,
            created_at=invite.created_at,
            expires_at=invite.expires_at,
        )
        for invite in invites
    ]