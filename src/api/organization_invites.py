from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta
import secrets
import hashlib
import hmac

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session

from src.api.auth import get_current_user
from src.database.deps import get_db
from src.models.organization import Organization
from src.models.organization_member import OrganizationMember
from src.models.organization_invite import OrganizationInvite
from src.models.user import User

router = APIRouter(prefix="/organizations", tags=["Organization Invites"])

INVITE_TTL_DAYS = 7


# =========================================================
# Schemas
# =========================================================

class CreateInviteRequest(BaseModel):
    email: EmailStr
    role: str = Field(default="member", min_length=1, max_length=20)


class InviteResponse(BaseModel):
    id: str
    organization_id: str
    email: str
    role: str
    status: str
    invited_by_user_id: Optional[str]
    accepted_by_user_id: Optional[str]
    created_at: str
    expires_at: str
    accepted_at: Optional[str]
    revoked_at: Optional[str]


class CreateInviteResponse(InviteResponse):
    """
    Returned only when:
    - creating a brand-new invite
    - resending (rotating token) for a pending invite

    Token is returned ONLY in these two cases.
    """
    token: str
    invite_link: str


# =========================================================
# Helpers
# =========================================================

def normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def build_invite_link(invite_id: UUID, token: str) -> str:
    # Relative link so you can copy/paste into curl
    return f"/v1/organizations/invites/{invite_id}/accept?token={token}"


def require_org_role(
    organization_id: UUID,
    db: Session,
    user: User,
    required_role: str = "admin",
) -> Organization:
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # owner is always allowed
    if org.owner_id == user.id:
        return org

    member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user.id,
        )
        .first()
    )

    if not member:
        raise HTTPException(status_code=403, detail="Not an organization member")

    if required_role == "admin" and member.role not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="Requires org role: admin")

    return org


def to_invite_response(inv: OrganizationInvite) -> InviteResponse:
    return InviteResponse(
        id=str(inv.id),
        organization_id=str(inv.organization_id),
        email=inv.email,
        role=inv.role,
        status=inv.status,
        invited_by_user_id=str(inv.invited_by_user_id) if inv.invited_by_user_id else None,
        accepted_by_user_id=str(inv.accepted_by_user_id) if inv.accepted_by_user_id else None,
        created_at=inv.created_at.isoformat(),
        expires_at=inv.expires_at.isoformat(),
        accepted_at=inv.accepted_at.isoformat() if inv.accepted_at else None,
        revoked_at=inv.revoked_at.isoformat() if inv.revoked_at else None,
    )


def _rotate_token(inv: OrganizationInvite) -> str:
    """
    Rotates token + extends expiry.
    Returns the NEW plaintext token.
    """
    plaintext_token = "oi_" + secrets.token_urlsafe(32)
    inv.token_hash = hash_token(plaintext_token)
    inv.token_prefix = plaintext_token[:10]
    inv.expires_at = datetime.now(timezone.utc) + timedelta(days=INVITE_TTL_DAYS)
    return plaintext_token


# =========================================================
# Routes
# =========================================================

@router.post("/{organization_id}/invites", response_model=CreateInviteResponse)
def create_invite(
    organization_id: UUID,
    payload: CreateInviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _org = require_org_role(organization_id, db, current_user, "admin")

    email_norm = normalize_email(str(payload.email))

    # Prevent inviting existing members
    user_row = db.query(User).filter(User.email == email_norm).first()
    if user_row:
        existing_member = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == user_row.id,
            )
            .first()
        )
        if existing_member:
            raise HTTPException(status_code=409, detail="User is already an organization member")

    # Prevent duplicate pending invite
    pending = (
        db.query(OrganizationInvite)
        .filter(
            OrganizationInvite.organization_id == organization_id,
            OrganizationInvite.email == email_norm,
            OrganizationInvite.status == "pending",
        )
        .first()
    )
    if pending:
        raise HTTPException(status_code=409, detail="Pending invite already exists")

    now = datetime.now(timezone.utc)

    plaintext_token = "oi_" + secrets.token_urlsafe(32)

    inv = OrganizationInvite(
        organization_id=organization_id,
        email=email_norm,
        role=payload.role,
        status="pending",
        invited_by_user_id=current_user.id,
        created_at=now,
        expires_at=now + timedelta(days=INVITE_TTL_DAYS),
        token_hash=hash_token(plaintext_token),
        token_prefix=plaintext_token[:10],
    )

    db.add(inv)
    db.commit()
    db.refresh(inv)

    base = to_invite_response(inv)
    return CreateInviteResponse(
        **base.model_dump(),
        token=plaintext_token,
        invite_link=build_invite_link(inv.id, plaintext_token),
    )


@router.get("/{organization_id}/invites", response_model=List[InviteResponse])
def list_invites(
    organization_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _org = require_org_role(organization_id, db, current_user, "admin")

    invites = (
        db.query(OrganizationInvite)
        .filter(OrganizationInvite.organization_id == organization_id)
        .order_by(OrganizationInvite.created_at.desc())
        .all()
    )

    return [to_invite_response(i) for i in invites]


@router.post("/invites/{invite_id}/resend", response_model=CreateInviteResponse)
def resend_invite(
    invite_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Admin-only. Rotates token + extends expiry for a PENDING invite.
    Returns the NEW token ONCE (like "email resend").
    """
    inv = db.query(OrganizationInvite).filter(OrganizationInvite.id == invite_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invite not found")

    _org = require_org_role(inv.organization_id, db, current_user, "admin")

    if inv.status != "pending":
        raise HTTPException(status_code=409, detail=f"Invite is {inv.status}")

    new_token = _rotate_token(inv)

    db.commit()
    db.refresh(inv)

    base = to_invite_response(inv)
    return CreateInviteResponse(
        **base.model_dump(),
        token=new_token,
        invite_link=build_invite_link(inv.id, new_token),
    )


@router.post("/invites/{invite_id}/accept", response_model=InviteResponse)
def accept_invite(
    invite_id: UUID,
    token: str = Query(..., min_length=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inv = db.query(OrganizationInvite).filter(OrganizationInvite.id == invite_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invite not found")

    now = datetime.now(timezone.utc)

    # Token validation FIRST (prevents state leaks)
    if not hmac.compare_digest(hash_token(token), inv.token_hash):
        raise HTTPException(status_code=403, detail="Invalid invite token")

    if inv.status != "pending":
        raise HTTPException(status_code=409, detail=f"Invite is {inv.status}")

    if inv.expires_at <= now:
        raise HTTPException(status_code=410, detail="Invite expired")

    if inv.email.lower() != current_user.email.lower():
        raise HTTPException(status_code=403, detail="Invite email does not match your account")

    existing_member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == inv.organization_id,
            OrganizationMember.user_id == current_user.id,
        )
        .first()
    )

    if not existing_member:
        db.add(
            OrganizationMember(
                organization_id=inv.organization_id,
                user_id=current_user.id,
                role="admin" if inv.role == "admin" else "member",
            )
        )

    inv.status = "accepted"
    inv.accepted_by_user_id = current_user.id
    inv.accepted_at = now

    db.commit()
    db.refresh(inv)

    return to_invite_response(inv)


@router.post("/invites/{invite_id}/revoke", response_model=InviteResponse)
def revoke_invite(
    invite_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inv = db.query(OrganizationInvite).filter(OrganizationInvite.id == invite_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invite not found")

    _org = require_org_role(inv.organization_id, db, current_user, "admin")

    if inv.status != "pending":
        raise HTTPException(status_code=409, detail=f"Invite is {inv.status}")

    inv.status = "revoked"
    inv.revoked_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(inv)

    return to_invite_response(inv)