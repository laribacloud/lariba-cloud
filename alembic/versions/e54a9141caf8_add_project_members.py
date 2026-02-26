"""add project members

Revision ID: e54a9141caf8
Revises: a92e8121287f
Create Date: <auto>

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e54a9141caf8"
down_revision: Union[str, Sequence[str], None] = "a92e8121287f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_members",
        sa.Column("project_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id", "user_id"),
    )
    op.create_index("ix_project_members_user_id", "project_members", ["user_id"])
    op.create_index("ix_project_members_project_id", "project_members", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_project_members_project_id", table_name="project_members")
    op.drop_index("ix_project_members_user_id", table_name="project_members")
    op.drop_table("project_members")
