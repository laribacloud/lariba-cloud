from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.api.auth import get_current_user
from src.database.deps import get_db
from src.models.project import Project
from src.models.project_member import ProjectMember
from src.models.user import User

router = APIRouter(prefix="/projects", tags=["Projects"])


class CreateProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(min_length=1, max_length=200)


class ProjectResponse(BaseModel):
    id: str
    name: str
    slug: str
    owner_id: str
    created_at: str


@router.post("", response_model=ProjectResponse)
def create_project(
    payload: CreateProjectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Project).filter(Project.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Slug already exists")

    project = Project(
        name=payload.name,
        slug=payload.slug,
        owner_id=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Owner becomes an admin member as well (organization layer)
    member = ProjectMember(project_id=project.id, user_id=current_user.id, role="admin")
    db.add(member)
    db.commit()

    return ProjectResponse(
        id=str(project.id),
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
        .outerjoin(ProjectMember, ProjectMember.project_id == Project.id)
        .filter(
            (Project.owner_id == current_user.id)
            | (ProjectMember.user_id == current_user.id)
        )
        # Postgres DISTINCT ON requires ORDER BY to start with the DISTINCT ON columns
        .distinct(Project.id)
        .order_by(Project.id, Project.created_at.desc())
        .all()
    )

    return [
        ProjectResponse(
            id=str(p.id),
            name=p.name,
            slug=p.slug,
            owner_id=str(p.owner_id),
            created_at=p.created_at.isoformat(),
        )
        for p in projects
    ]