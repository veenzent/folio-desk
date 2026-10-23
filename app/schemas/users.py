from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserInternalResponse(BaseModel):
    id: UUID
    client_id: str | None
    email: str | None
    password_hash: str
    role: str
    is_active: bool
    created_at: datetime
    # all other fields needed ...

    class Config:
        from_attributes = True


class UserExternalResponse(BaseModel):
    id: UUID
    email_address: str

    class Config:
        from_attributes = True

    @classmethod
    def from_internal(cls, user: "UserInternalResponse") -> "UserExternalResponse":
        return cls(
            id=user.id,
            email_address=user.email or "",
        )


class TokenData(BaseModel):
    email_address: str | None = None


class OTPPurpose(str):
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
