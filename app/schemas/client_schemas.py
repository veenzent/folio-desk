from pydantic import BaseModel


class AddClient(BaseModel):
    name: str
    contact_email: str
    tier: str


class AddClientResponse(BaseModel):
    id: str | None = None
    name: str
    contact_email: str
    tier: str
    created_at: str
    updated_at: str
