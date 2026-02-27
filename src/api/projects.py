from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.auth import get_current_user
from src.database.deps import get_db
from src.models.organization import Organization
from src.models.organization_member import OrganizationMember
from src.models.project import Project
from src.models.project_member import ProjectMember
from src.models.user import User

router = APIRouter(prefix="/projects", tags=["Projects"])


class CreateProjectRequest(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200)


class ProjectResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    slug: str
    owner_id: str
    created_at: str


def require_org_member(org_id: UUID, db: Session, user: User) -> Organization:
    """
    Policy B1:
    - Any organization member (role: owner/admin/member) can create projects.
    - Must at least be a member.
    """
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    membership = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user.id,
        )
        .first()
    )

    # If you allow implicit membership via org.owner_id, keep this:
    if org.owner_id == user.id and membership is None:
        # owner exists but membership row missing; treat as allowed
        return org

    if membership is None:
        raise HTTPException(status_code=403, detail="Not an organization member")

    return org


@router.post("", response_model=ProjectResponse)
def create_project(
    payload: CreateProjectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ✅ B1: must be org member (not necessarily admin)
    _org = require_org_member(payload.organization_id, db=db, user=current_user)

    # Slug unique (global)
    existing = db.query(Project).filter(Project.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Slug already exists")

    project = Project(
        organization_id=payload.organization_id,
        name=payload.name,
        slug=payload.slug,
        owner_id=current_user.id,  # keep for now
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Creator becomes project admin
    db.add(ProjectMember(project_id=project.id, user_id=current_user.id, role="admin"))
    db.commit()

    return ProjectResponse(
        id=str(project.id),
        organization_id=str(project.organization_id),
        name=project.name,
        slug=project.slug,
        owner_id=str(project.owner_id),
        created_at=project.created_at.isoformat(),
    )


@router.get("", response_model=List[ProjectResponse])
def list_my_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # list projects where you're a project member
    projects = (
        db.query(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .filter(ProjectMember.user_id == current_user.id)
        .order_by(Project.created_at.desc())
        .all()
    )

    return [
        ProjectResponse(
            id=str(p.id),
            organization_id=str(p.organization_id),
            name=p.name,
            slug=p.slug,
            owner_id=str(p.owner_id),
            created_at=p.created_at.isoformat(),
        )
        for p in projects
    ]