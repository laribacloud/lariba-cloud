from typing import List, Optional
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

router = APIRouter(prefix="/projects", tags=["Project Members"])


# =========================
# Schemas
# =========================

class ProjectMemberResponse(BaseModel):
    project_id: str
    user_id: str
    role: str
    created_at: str


class AddProjectMemberRequest(BaseModel):
    user_id: UUID
    role: str = Field(default="member", min_length=1, max_length=20)


class UpdateProjectMemberRoleRequest(BaseModel):
    role: str = Field(min_length=1, max_length=20)


# =========================
# Helpers
# =========================

def require_project_member(
    project_id: UUID,
    db: Session,
    user: User,
) -> tuple[Project, ProjectMember]:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    membership = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not a project member")

    return project, membership


def require_project_admin(
    project_id: UUID,
    db: Session,
    user: User,
) -> tuple[Project, ProjectMember]:
    project, membership = require_project_member(project_id, db=db, user=user)
    if membership.role != "admin":
        raise HTTPException(status_code=403, detail="Project admin required")
    return project, membership


# =========================
# Routes
# =========================

@router.get("/{project_id}/members", response_model=List[ProjectMemberResponse])
def list_project_members(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Any project member can list members
    _project, _me = require_project_member(project_id, db=db, user=current_user)

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


@router.get("/{project_id}/members/me", response_model=ProjectMemberResponse)
def my_project_membership(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _project, membership = require_project_member(project_id, db=db, user=current_user)

    return ProjectMemberResponse(
        project_id=str(membership.project_id),
        user_id=str(membership.user_id),
        role=membership.role,
        created_at=membership.created_at.isoformat(),
    )


@router.post("/{project_id}/members", response_model=ProjectMemberResponse)
def add_project_member(
    project_id: UUID,
    payload: AddProjectMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Only project admin can add members
    _project, _me = require_project_admin(project_id, db=db, user=current_user)

    # Ensure user exists
    target_user = db.query(User).filter(User.id == payload.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == payload.user_id,
        )
        .first()
    )

    now = datetime.now(timezone.utc)

    if existing:
        # Upsert behavior: update role
        existing.role = payload.role
        db.commit()
        db.refresh(existing)
        return ProjectMemberResponse(
            project_id=str(existing.project_id),
            user_id=str(existing.user_id),
            role=existing.role,
            created_at=existing.created_at.isoformat(),
        )

    member = ProjectMember(
        project_id=project_id,
        user_id=payload.user_id,
        role=payload.role,
        created_at=now,
    )
    db.add(member)
    db.commit()
    db.refresh(member)

    return ProjectMemberResponse(
        project_id=str(member.project_id),
        user_id=str(member.user_id),
        role=member.role,
        created_at=member.created_at.isoformat(),
    )


@router.patch("/{project_id}/members/{user_id}", response_model=ProjectMemberResponse)
def update_project_member_role(
    project_id: UUID,
    user_id: UUID,
    payload: UpdateProjectMemberRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Only project admin can change roles
    _project, _me = require_project_admin(project_id, db=db, user=current_user)

    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Project member not found")

    member.role = payload.role
    db.commit()
    db.refresh(member)

    return ProjectMemberResponse(
        project_id=str(member.project_id),
        user_id=str(member.user_id),
        role=member.role,
        created_at=member.created_at.isoformat(),
    )


@router.delete("/{project_id}/members/{user_id}")
def remove_project_member(
    project_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Only project admin can remove members
    _project, _me = require_project_admin(project_id, db=db, user=current_user)

    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Project member not found")

    db.delete(member)
    db.commit()
    return {"message": "Project member removed"}
