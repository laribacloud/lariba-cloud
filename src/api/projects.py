import re
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, constr
from sqlalchemy.orm import Session
from uuid import UUID

from src.database.deps import get_db
from src.models.project import Project
from src.services.security import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])


def slugify(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "project"


class ProjectCreate(BaseModel):
    name: constr(min_length=2, max_length=60)


class ProjectOut(BaseModel):
    id: UUID
    name: str
    slug: str
    owner_id: UUID

    class Config:
        from_attributes = True


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    base_slug = slugify(payload.name)

    slug = base_slug
    n = 1
    while db.query(Project).filter(Project.owner_id == current_user.id, Project.slug == slug).first():
        n += 1
        slug = f"{base_slug}-{n}"

    project = Project(owner_id=current_user.id, name=payload.name, slug=slug)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return (
        db.query(Project)
        .filter(Project.owner_id == current_user.id)
        .order_by(Project.created_at.desc())
        .all()
    )


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    return project
