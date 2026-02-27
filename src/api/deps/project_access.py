from typing import Tuple
from uuid import UUID

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.auth import get_current_user
from src.database.deps import get_db
from src.models.project import Project
from src.models.project_member import ProjectMember
from src.models.user import User


def _get_project(db: Session, project_id: UUID) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def require_project_member(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Tuple[Project, ProjectMember]:
    """
    Requires the current user to be a member of the project (admin OR member).
    Returns: (project, membership)
    """
    project = _get_project(db, project_id)

    membership = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a project member")

    return project, membership


def require_project_admin(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Tuple[Project, ProjectMember]:
    """
    Requires the current user to be an admin of the project.
    Returns: (project, membership)
    """
    project, membership = require_project_member(
        project_id=project_id, db=db, current_user=current_user
    )

    if membership.role != "admin":
        raise HTTPException(status_code=403, detail="Project admin required")

    return project, membership