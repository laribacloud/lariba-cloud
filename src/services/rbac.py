from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.models.organization import Organization
from src.models.organization_member import OrganizationMember
from src.models.project import Project
from src.models.project_member import ProjectMember
from src.models.user import User


ORG_ROLE_ORDER = {"member": 1, "admin": 2, "owner": 3}
PROJECT_ROLE_ORDER = {"member": 1, "admin": 2}


def require_org_role(
    org_id: UUID,
    *,
    db: Session,
    current_user: User,
    min_role: str,
) -> Organization:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Owner always passes
    if org.owner_id == current_user.id:
        return org

    membership = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == current_user.id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(status_code=403, detail="Not an organization member")

    if ORG_ROLE_ORDER.get(membership.role, 0) < ORG_ROLE_ORDER[min_role]:
        raise HTTPException(status_code=403, detail=f"Requires org role: {min_role}")

    return org


def require_project_role(
    project_id: UUID,
    *,
    db: Session,
    current_user: User,
    min_role: str,
) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # If you own the org, you are effectively admin everywhere
    if project.organization and project.organization.owner_id == current_user.id:
        return project

    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=403, detail="Not a project member")

    if PROJECT_ROLE_ORDER.get(member.role, 0) < PROJECT_ROLE_ORDER[min_role]:
        raise HTTPException(status_code=403, detail=f"Requires project role: {min_role}")

    return project
