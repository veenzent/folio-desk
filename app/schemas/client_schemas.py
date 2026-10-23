from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from app.models.enums import ClientTier


class AddClient(BaseModel):
    name: str
    contact_email: str


class AddClientResponse(BaseModel):
    id: UUID | None = None
    name: str
    contact_email: str
    tier: ClientTier
    created_at: datetime
    updated_at: datetime
