from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, constr
from sqlalchemy.orm import Session
from uuid import UUID

from src.database.deps import get_db
from src.models.project import Project
from src.models.api_key import ApiKey
from src.services.security import get_current_user
from src.services.api_keys import generate_api_key, hash_api_key, key_prefix


router = APIRouter(prefix="/projects", tags=["api-keys"])


class ApiKeyCreate(BaseModel):
    name: constr(min_length=2, max_length=50)


class ApiKeyOut(BaseModel):
    id: UUID
    name: str
    key_prefix: str

    class Config:
        from_attributes = True


class ApiKeyCreated(BaseModel):
    id: UUID
    name: str
    key_prefix: str
    api_key: str  # raw key (ONLY returned once)


@router.post("/{project_id}/keys", response_model=ApiKeyCreated, status_code=201)
def create_project_key(
    project_id: UUID,
    payload: ApiKeyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    raw = generate_api_key()
    hashed = hash_api_key(raw)
    prefix = key_prefix(raw)

    # extremely unlikely collision, but safe to check
    exists = db.query(ApiKey).filter(ApiKey.key_hash == hashed).first()
    if exists:
        raise HTTPException(status_code=500, detail="Key generation collision, retry")

    key = ApiKey(project_id=project.id, name=payload.name, key_prefix=prefix, key_hash=hashed)
    db.add(key)
    db.commit()
    db.refresh(key)

    return ApiKeyCreated(id=key.id, name=key.name, key_prefix=key.key_prefix, api_key=raw)


@router.get("/{project_id}/keys", response_model=list[ApiKeyOut])
def list_project_keys(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    return db.query(ApiKey).filter(ApiKey.project_id == project.id).order_by(ApiKey.created_at.desc()).all()


@router.delete("/{project_id}/keys/{key_id}", status_code=204)
def delete_project_key(
    project_id: UUID,
    key_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    key = db.query(ApiKey).filter(ApiKey.id == key_id, ApiKey.project_id == project.id).first()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")

    db.delete(key)
    db.commit()
    return None
