from uuid import UUID

from pydantic import BaseModel


class UserInternalResponse(BaseModel):
    id: UUID
    email_address: str | None
    phone_number: str | None
    password_hash: str
    is_active: bool
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
