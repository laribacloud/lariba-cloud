from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database.db import Base


class Organization(Base):
    __tablename__ = "organizations"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True, index=True)

    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # relationships
    owner = relationship("User")

    members = relationship(
        "OrganizationMember",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    # ✅ THIS FIXES YOUR ERROR (something expects Organization.projects)
    projects = relationship(
        "Project",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    # invites (Policy A)
    invites = relationship(
        "OrganizationInvite",
        back_populates="organization",
        cascade="all, delete-orphan",
    )