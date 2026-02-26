from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database.db import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    name = Column(String, nullable=False, default="You")
    email = Column(String, nullable=False, unique=True, index=True)
    password_hash = Column(String, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Owner relationship
    projects = relationship("Project", back_populates="owner")

    # Membership relationship
    project_memberships = relationship(
        "ProjectMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )