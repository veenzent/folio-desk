from datetime import datetime
from pydantic import BaseModel

from app.models.enums import UserRole


class AddAdmin(BaseModel):
    email: str
    password: str


class AddAdminRole(BaseModel):
    email: str
    password: str
    role: UserRole

class AddAdminResponse(BaseModel):
    email: str
    message: str


class RegisterRequest(BaseModel):
    invite_code: str
    email: str
    password: str
    # TODO: confirm_password: str

class RegisterRequestResponse(BaseModel):
    id: str | None = None
    email: str
    role: str
    client_id: str
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

