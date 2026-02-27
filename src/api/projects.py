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


# =========================================================
# Schemas
# =========================================================

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


class AddProjectMemberRequest(BaseModel):
    user_id: UUID
    role: str = Field(default="member", min_length=1, max_length=20)  # "admin" | "member"


class UpdateProjectMemberRequest(BaseModel):
    role: str = Field(min_length=1, max_length=20)  # "admin" | "member"


class ProjectMemberResponse(BaseModel):
    project_id: str
    user_id: str
    role: str
    created_at: str


# =========================================================
# Permission helpers
# =========================================================

def require_org_member(org_id: UUID, db: Session, user: User) -> Organization:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if org.owner_id == user.id:
        return org

    is_member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user.id,
        )
        .first()
        is not None
    )
    if not is_member:
        raise HTTPException(status_code=403, detail="Not an organization member")

    return org


def require_org_admin(org: Organization, db: Session, user: User) -> None:
    """Org owner or OrganizationMember.role == 'admin' or 'owner'."""
    if org.owner_id == user.id:
        return

    membership = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == org.id,
            OrganizationMember.user_id == user.id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not an organization member")

    if membership.role not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Requires org role: admin")


def require_project_member(project_id: UUID, db: Session, user: User) -> ProjectMember:
    pm = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user.id)
        .first()
    )
    if not pm:
        raise HTTPException(status_code=403, detail="Not a project member")
    return pm


def require_project_admin_or_org_admin(project: Project, db: Session, user: User) -> None:
    """Project admin OR org admin (or org owner) can manage members."""
    # project admin?
    pm = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project.id, ProjectMember.user_id == user.id)
        .first()
    )
    if pm and pm.role == "admin":
        return

    # else org admin?
    org = db.query(Organization).filter(Organization.id == project.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    require_org_admin(org, db=db, user=user)


# =========================================================
# Project routes
# =========================================================

@router.post("", response_model=ProjectResponse)
def create_project(
    payload: CreateProjectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = require_org_member(payload.organization_id, db=db, user=current_user)

    # Only org admin/owner can create projects (recommended)
    require_org_admin(org, db=db, user=current_user)

    # slug unique (global)
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

    # creator becomes admin member
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


# =========================================================
# Project member management (Step 7)
# =========================================================

@router.get("/{project_id}/members", response_model=List[ProjectMemberResponse])
def list_project_members(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # any project member can list members
    _ = require_project_member(project_id, db=db, user=current_user)

    members = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id)
        .order_by(ProjectMember.created_at.asc())
        .all()
    )

    return [
        ProjectMemberResponse(
            project_id=str(m.project_id),
            user_id=str(m.user_id),
            role=m.role,
            created_at=m.created_at.isoformat(),
        )
        for m in members
    ]


@router.post("/{project_id}/members", response_model=ProjectMemberResponse)
def add_project_member(
    project_id: UUID,
    payload: AddProjectMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.role not in ("admin", "member"):
        raise HTTPException(status_code=400, detail="Invalid role")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # project admin OR org admin can add members
    require_project_admin_or_org_admin(project, db=db, user=current_user)

    # ensure target user exists
    target = db.query(User).filter(User.id == payload.user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    # ensure target is org member (basic rule)
    target_org_membership = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == project.organization_id,
            OrganizationMember.user_id == payload.user_id,
        )
        .first()
    )
    org = db.query(Organization).filter(Organization.id == project.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if not (org.owner_id == payload.user_id or target_org_membership is not None):
        raise HTTPException(status_code=403, detail="User is not in the organization")

    existing = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == payload.user_id)
        .first()
    )
    if existing:
        # idempotent
        return ProjectMemberResponse(
            project_id=str(existing.project_id),
            user_id=str(existing.user_id),
            role=existing.role,
            created_at=existing.created_at.isoformat(),
        )

    pm = ProjectMember(project_id=project_id, user_id=payload.user_id, role=payload.role)
    db.add(pm)
    db.commit()
    db.refresh(pm)

    return ProjectMemberResponse(
        project_id=str(pm.project_id),
        user_id=str(pm.user_id),
        role=pm.role,
        created_at=pm.created_at.isoformat(),
    )


@router.patch("/{project_id}/members/{user_id}", response_model=ProjectMemberResponse)
def update_project_member_role(
    project_id: UUID,
    user_id: UUID,
    payload: UpdateProjectMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.role not in ("admin", "member"):
        raise HTTPException(status_code=400, detail="Invalid role")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    require_project_admin_or_org_admin(project, db=db, user=current_user)

    pm = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        .first()
    )
    if not pm:
        raise HTTPException(status_code=404, detail="Project member not found")

    pm.role = payload.role
    db.commit()
    db.refresh(pm)

    return ProjectMemberResponse(
        project_id=str(pm.project_id),
        user_id=str(pm.user_id),
        role=pm.role,
        created_at=pm.created_at.isoformat(),
    )


@router.delete("/{project_id}/members/{user_id}")
def remove_project_member(
    project_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    require_project_admin_or_org_admin(project, db=db, user=current_user)

    pm = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        .first()
    )
    if not pm:
        return {"message": "User is not a member"}

    db.delete(pm)
    db.commit()
    return {"message": "Member removed"}