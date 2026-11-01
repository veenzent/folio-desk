from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class CreateInvite(BaseModel):
    client_id: str


class AddInviteData(BaseModel):
    id: UUID
    client_id: UUID
    code_hash: str
    expires_at: str
    used_at: str | None
    revoked_at: datetime | None
    created_at: datetime


class InviteResponse(BaseModel):
    id: str
    client_id: str
    invite_code: str
    created_at: datetime
    expires_at: datetime

