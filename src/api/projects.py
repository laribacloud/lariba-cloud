from typing import List
from uuid import UUID

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.auth import get_current_user
from src.database.deps import get_db
from src.models.project import Project
from src.models.project_member import ProjectMember
from src.models.user import User
from src.services.rbac import require_org_role

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


# =========================================================
# Routes
# =========================================================

@router.post("", response_model=ProjectResponse)
def create_project(
    payload: CreateProjectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Option A: require org admin (or owner) to create projects
    _org = require_org_role(
        payload.organization_id,
        db=db,
        current_user=current_user,
        min_role="admin",
    )

    # Slug unique (global)
    existing = db.query(Project).filter(Project.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Slug already exists")

    now = datetime.now(timezone.utc)

    project = Project(
        organization_id=payload.organization_id,
        name=payload.name,
        slug=payload.slug,
        owner_id=current_user.id,  # keep for legacy compatibility / convenience
        created_at=now,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Creator becomes an admin member of the project
    member = ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role="admin",
        created_at=now,
    )
    db.add(member)
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
    # Simple: list projects where you are a project member
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