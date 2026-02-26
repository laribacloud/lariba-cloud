"""add organizations

Revision ID: ac623d506dc1
Revises: a92e8121287f
Create Date: 2026-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "ac623d506dc1"
down_revision: Union[str, Sequence[str], None] = "a92e8121287f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- organizations table ---
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)
    op.create_index("ix_organizations_owner_id", "organizations", ["owner_id"], unique=False)

    # --- add organization_id to projects (nullable for now, to backfill later) ---
    op.add_column("projects", sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_projects_organization_id", "projects", ["organization_id"], unique=False)
    op.create_foreign_key(
        "projects_organization_id_fkey",
        "projects",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("projects_organization_id_fkey", "projects", type_="foreignkey")
    op.drop_index("ix_projects_organization_id", table_name="projects")
    op.drop_column("projects", "organization_id")

    op.drop_index("ix_organizations_owner_id", table_name="organizations")
    op.drop_index("ix_organizations_slug", table_name="organizations")
    op.drop_table("organizations")