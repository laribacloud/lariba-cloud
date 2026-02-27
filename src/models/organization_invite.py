from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database.db import Base


class OrganizationInvite(Base):
    """
    Policy A1: Invite-by-email, but accept requires the user already has an account
    (we match the invite email to the current_user.email).
    """
    __tablename__ = "organization_invites"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "email",
            "status",
            name="uq_org_invite_org_email_status",
        ),
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
