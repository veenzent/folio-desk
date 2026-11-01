from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import RateLimit
from app.core.security import get_db, get_current_admin
from app.schemas.invite_schemas import CreateInvite, AddInviteData, InviteResponse
from app.services.invite_services import create_invitation, get_all_invites
# from app.services.invite_services import 

router = APIRouter(prefix="/invites")


@router.post(
    "",
    summary="Create an invitation for a client",
    dependencies=[Depends(RateLimit(times=10, seconds=60)), Depends(get_current_admin)],
    response_model=InviteResponse,
)
async def create_invite(
    invite: CreateInvite,
    db: AsyncSession = Depends(get_db),
) -> InviteResponse:
    """
    Admin only route to create invitations.
    """
    created_invite = await create_invitation(invite.client_id, db)

    return created_invite


@router.get(
    "",
    summary="Get all invitations",
    dependencies=[Depends(RateLimit(times=10, seconds=60)), Depends(get_current_admin)],
    response_model=list[InviteResponse],
)
async def get_invites(
    db: AsyncSession = Depends(get_db),
    # add page size and page number for pagination
) -> list | list[InviteResponse]:
    """
    Admin only route to get all invitations.
    """
    invites = await get_all_invites(db)

    return invites


@router.delete(
    "/{invite_id}",
    deprecated=True,
    summary="Delete an invitation by ID",
    dependencies=[Depends(RateLimit(times=10, seconds=60)), Depends(get_current_admin)],
    response_model=InviteResponse,
)
async def delete_invite_by_id(
    invite_id: str,
    db: AsyncSession = Depends(get_db),
) -> InviteResponse:
    """
    Admin only route to delete an invitation by ID.
    """
    pass

