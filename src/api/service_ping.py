from fastapi import APIRouter, Depends
from src.models.project import Project
from src.services.api_key_auth import get_project_from_api_key

router = APIRouter(prefix="/service", tags=["service"])


@router.get("/ping")
def service_ping(project: Project = Depends(get_project_from_api_key)):
    return {
        "ok": True,
        "project_id": str(project.id),
        "project_slug": project.slug,
        "message": "API key authenticated successfully",
    }
