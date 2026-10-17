from uuid import UUID

from pydantic import BaseModel


class UserInternalResponse(BaseModel):
    id: UUID
    client_id: str
    email: str | None
    password_hash: str
    role: str
    is_active: bool
    created_at: str
    # all other fields needed ...

    class Config:
        from_attributes = True


class UserExternalResponse(BaseModel):
    id: UUID
    email_address: str

    class Config:
        from_attributes = True


class TokenData(BaseModel):
    email_address: str | None = None


class OTPPurpose(str):
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
