from pydantic import BaseModel
from app.models.enums import ClientTier


class AddClient(BaseModel):
    name: str
    contact_email: str
    tier: ClientTier


class AddClientResponse(BaseModel):
    id: str | None = None
    name: str
    contact_email: str
    tier: ClientTier
    created_at: str
    updated_at: str
