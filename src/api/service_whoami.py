from typing import Tuple

from fastapi import APIRouter, Depends

from src.api.api_keys import get_project_and_key_from_api_key, require_scope
from src.models.api_key import ApiKey
from src.models.project import Project

router = APIRouter(prefix="/service", tags=["Service"])


@router.get("/whoami")
def whoami(auth: Tuple[Project, ApiKey] = Depends(get_project_and_key_from_api_key)):
    project, key = auth
    return {
        "project_id": str(project.id),
        "project_slug": project.slug,
        "project_name": project.name,
        "api_key_id": str(key.id),
        "scope": key.scope,
    }


@router.get("/admin-only")
def admin_only(auth: Tuple[Project, ApiKey] = Depends(require_scope("admin"))):
    project, key = auth
    return {"message": "Admin access granted", "project_slug": project.slug}