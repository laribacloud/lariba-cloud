from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database.db import Base


class OrganizationInvite(Base):
    """
    Policy A1: Invite-by-email.
    Accept requires:
      1) user already has an account AND email matches invite.email
      2) caller provides invite token (hashed in DB)
      3) invite is not expired
    """
    __tablename__ = "organization_invites"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "email",
            "status",
            name="uq_org_invite_org_email_status",
        ),
        Index("ix_org_invites_org_email_status", "organization_id", "email", "status"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Invitee email (must match User.email when accepting)
    email = Column(String, nullable=False, index=True)

    # "admin" | "member"
    role = Column(String(20), nullable=False, default="member")

    # "pending" | "accepted" | "revoked"
    status = Column(String(20), nullable=False, default="pending", index=True)

    # Token is generated at creation, returned ONCE, and only hash is stored.
    token_prefix = Column(String(12), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)  # sha256 hex

    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    invited_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    accepted_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    accepted_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    organization = relationship("Organization", back_populates="invites")
    invited_by = relationship("User", foreign_keys=[invited_by_user_id])
    accepted_by = relationship("User", foreign_keys=[accepted_by_user_id])