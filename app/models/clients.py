from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum as SAEnum
from sqlalchemy import DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ClientTier

if TYPE_CHECKING:
    from app.models.invite_codes import InviteCodes
    from app.models.projects import Projects
    from app.models.users import Users


class Clients(Base):
    __tablename__ = "clients"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    tier: Mapped[ClientTier] = mapped_column(
        SAEnum(
            ClientTier,
            name="client_tier",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=text("'standard'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()"),
    )

    users: Mapped[list[Users]] = relationship(back_populates="client")
    invite_codes: Mapped[list[InviteCodes]] = relationship(back_populates="client")
    projects: Mapped[list[Projects]] = relationship(back_populates="client")