from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.auth import get_current_user
from src.database.deps import get_db
from src.models.organization import Organization
from src.models.organization_member import OrganizationMember
from src.models.user import User

router = APIRouter(prefix="/organizations", tags=["Organizations"])


class CreateOrganizationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200)


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    owner_id: str
    created_at: str


class AddMemberRequest(BaseModel):
    user_id: UUID
    role: str = Field(default="member", min_length=1, max_length=50)


@router.post("", response_model=OrganizationResponse)
def create_organization(
    payload: CreateOrganizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Organization).filter(Organization.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Slug already exists")

    org = Organization(
        name=payload.name,
        slug=payload.slug,
        owner_id=current_user.id,
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    # ensure owner is also a member
    db.add(
        OrganizationMember(
            organization_id=org.id,
            user_id=current_user.id,
            role="owner",
        )
    )
    db.commit()

    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        slug=org.slug,
        owner_id=str(org.owner_id),
        created_at=org.created_at.isoformat(),
    )


@router.get("", response_model=List[OrganizationResponse])
def list_my_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    orgs = (
        db.query(Organization)
        .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
        .filter(OrganizationMember.user_id == current_user.id)
        .order_by(Organization.created_at.desc())
        .all()
    )

    return [
        OrganizationResponse(
            id=str(o.id),
            name=o.name,
            slug=o.slug,
            owner_id=str(o.owner_id),
            created_at=o.created_at.isoformat(),
        )
        for o in orgs
    ]


@router.post("/{organization_id}/members")
def add_member(
    organization_id: UUID,
    payload: AddMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if org.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only org owner can add members")

    exists = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == payload.user_id,
        )
        .first()
    )
    if exists:
        return {"message": "User already a member"}

    db.add(
        OrganizationMember(
            organization_id=organization_id,
            user_id=payload.user_id,
            role=payload.role,
        )
    )
    db.commit()
    return {"message": "Member added"}
