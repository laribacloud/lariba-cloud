from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database.db import Base


class ApiKey(Base):
    __tablename__ = "api_keys"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # matches DB: NOT NULL
    name = Column(String, nullable=False)

    # matches DB: NOT NULL
    key_prefix = Column(String, nullable=False, index=True)

    # matches DB: NOT NULL
    key_hash = Column(String, nullable=False, unique=True, index=True)

    # matches DB: NOT NULL
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # matches DB: nullable
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # matches DB: NOT NULL
    scope = Column(String, nullable=False, default="default")

    # matches DB: nullable
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # matches your desired schema (now migrated): nullable
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # relationship
    project = relationship("Project", back_populates="api_keys")
