from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database.db import Base


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, index=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # relationships
    owner = relationship("User", back_populates="projects")

    # ✅ matching back_populates for Organization.projects
    organization = relationship("Organization", back_populates="projects")

    api_keys = relationship(
        "ApiKey",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    members = relationship(
        "ProjectMember",
        back_populates="project",
        cascade="all, delete-orphan",
    )