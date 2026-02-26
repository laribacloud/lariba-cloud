from typing import Optional, Tuple, List
from datetime import datetime, timezone
from uuid import UUID
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.auth import get_current_user
from src.database.deps import get_db
from src.models.api_key import ApiKey
from src.models.project import Project
from src.models.user import User
from src.services.api_keys import hash_api_key
from src.services.rbac import require_project_role

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


# =========================================================
# Schemas
# =========================================================

class CreateApiKeyRequest(BaseModel):
    project_id: UUID
    name: str = Field(min_length=1, max_length=200)
    scope: str = Field(default="default", min_length=1, max_length=100)
    expires_at: Optional[datetime] = None


class BootstrapAdminKeyRequest(BaseModel):
    project_id: UUID
    name: str = Field(min_length=1, max_length=200)
    expires_at: Optional[datetime] = None


class CreateApiKeyResponse(BaseModel):
    api_key_id: str
    project_id: str
    name: str
    scope: str
    key_prefix: str
    api_key: str
    expires_at: Optional[str]


class ApiKeyListItem(BaseModel):
    id: str
    name: str
    key_prefix: str
    scope: str
    created_at: str
    last_used_at: Optional[str]
    expires_at: Optional[str]
    revoked_at: Optional[str]


# =========================================================
# Machine auth: X-API-Key dependency
# =========================================================

def get_project_and_key_from_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> Tuple[Project, ApiKey]:

    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key")

    hashed = hash_api_key(x_api_key)
    key = db.query(ApiKey).filter(ApiKey.key_hash == hashed).first()
    if not key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    now = datetime.now(timezone.utc)

    if key.revoked_at is not None:
        raise HTTPException(status_code=401, detail="API key revoked")

    if key.expires_at is not None and key.expires_at <= now:
        raise HTTPException(status_code=401, detail="API key expired")

    project = db.query(Project).filter(Project.id == key.project_id).first()
    if not project:
        raise HTTPException(status_code=401, detail="Project not found")

    # best-effort last_used_at update
    key.last_used_at = now
    db.commit()
    db.refresh(key)

    return project, key


def require_scope(required_scope: str):
    """
    Dependency factory for MACHINE auth scope checks (X-API-Key).
    Usage: Depends(require_scope("admin"))
    """
    def dependency(
        auth: Tuple[Project, ApiKey] = Depends(get_project_and_key_from_api_key),
    ) -> Tuple[Project, ApiKey]:

        project, key = auth

        if key.scope != required_scope:
            raise HTTPException(status_code=403, detail=f"{required_scope} scope required")

        return project, key

    return dependency


# =========================================================
# Routes
# =========================================================

@router.get("/ping")
def ping():
    return {"pong": True}


# ---------------------------------------------------------
# Machine introspection
# ---------------------------------------------------------
@router.get("/me")
def me(auth: Tuple[Project, ApiKey] = Depends(get_project_and_key_from_api_key)):

    project, key = auth

    return {
        "project_id": str(project.id),
        "project_name": project.name,
        "api_key_id": str(key.id),
        "scope": key.scope,
        "created_at": key.created_at.isoformat(),
        "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
        "expires_at": key.expires_at.isoformat() if key.expires_at else None,
        "revoked_at": key.revoked_at.isoformat() if key.revoked_at else None,
    }


# ---------------------------------------------------------
# Bootstrap FIRST admin key
# ---------------------------------------------------------
@router.post("/bootstrap", response_model=CreateApiKeyResponse)
def bootstrap_admin_key(
    payload: BootstrapAdminKeyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # Require project admin (org owner will pass via RBAC)
    project = require_project_role(
        payload.project_id,
        db=db,
        current_user=current_user,
        min_role="admin",
    )

    existing_count = db.query(ApiKey).filter(ApiKey.project_id == project.id).count()
    if existing_count > 0:
        raise HTTPException(
            status_code=409,
            detail="Bootstrap only allowed when project has no API keys",
        )

    plaintext_key = "lk_" + secrets.token_urlsafe(32)
    key_hash = hash_api_key(plaintext_key)
    key_prefix = plaintext_key[:8]
    now = datetime.now(timezone.utc)

    api_key = ApiKey(
        project_id=project.id,
        name=payload.name,
        scope="admin",
        key_prefix=key_prefix,
        key_hash=key_hash,
        created_at=now,
        expires_at=payload.expires_at,
        revoked_at=None,
        last_used_at=None,
    )

    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return CreateApiKeyResponse(
        api_key_id=str(api_key.id),
        project_id=str(api_key.project_id),
        name=api_key.name,
        scope=api_key.scope,
        key_prefix=api_key.key_prefix,
        api_key=plaintext_key,
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
    )


# ---------------------------------------------------------
# Create API key (project admin only)
# ---------------------------------------------------------
@router.post("", response_model=CreateApiKeyResponse)
def create_api_key(
    payload: CreateApiKeyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    project = require_project_role(
        payload.project_id,
        db=db,
        current_user=current_user,
        min_role="admin",
    )

    plaintext_key = "lk_" + secrets.token_urlsafe(32)
    key_hash = hash_api_key(plaintext_key)
    key_prefix = plaintext_key[:8]
    now = datetime.now(timezone.utc)

    api_key = ApiKey(
        project_id=project.id,
        name=payload.name,
        scope=payload.scope,
        key_prefix=key_prefix,
        key_hash=key_hash,
        created_at=now,
        expires_at=payload.expires_at,
        revoked_at=None,
        last_used_at=None,
    )

    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return CreateApiKeyResponse(
        api_key_id=str(api_key.id),
        project_id=str(api_key.project_id),
        name=api_key.name,
        scope=api_key.scope,
        key_prefix=api_key.key_prefix,
        api_key=plaintext_key,
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
    )


# ---------------------------------------------------------
# List API keys (project admin only)
# ---------------------------------------------------------
@router.get("", response_model=List[ApiKeyListItem])
def list_api_keys(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    project = require_project_role(
        project_id,
        db=db,
        current_user=current_user,
        min_role="admin",
    )

    keys = (
        db.query(ApiKey)
        .filter(ApiKey.project_id == project.id)
        .order_by(ApiKey.created_at.desc())
        .all()
    )

    return [
        ApiKeyListItem(
            id=str(k.id),
            name=k.name,
            key_prefix=k.key_prefix,
            scope=k.scope,
            created_at=k.created_at.isoformat(),
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
            expires_at=k.expires_at.isoformat() if k.expires_at else None,
            revoked_at=k.revoked_at.isoformat() if k.revoked_at else None,
        )
        for k in keys
    ]


# ---------------------------------------------------------
# Revoke API key (project admin only)
# ---------------------------------------------------------
@router.post("/{api_key_id}/revoke")
def revoke_api_key(
    api_key_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    key = db.query(ApiKey).filter(ApiKey.id == api_key_id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    require_project_role(
        key.project_id,
        db=db,
        current_user=current_user,
        min_role="admin",
    )

    if key.revoked_at is not None:
        return {"message": "API key already revoked"}

    key.revoked_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "API key revoked successfully"}