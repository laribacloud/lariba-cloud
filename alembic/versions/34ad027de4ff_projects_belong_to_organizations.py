"""projects belong to organizations

Revision ID: 34ad027de4ff
Revises: b7265285c3d6
Create Date: 2026-02-26 18:43:09.916916
"""

from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "34ad027de4ff"
down_revision: Union[str, Sequence[str], None] = "b7265285c3d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(bind, table_name: str, column_name: str) -> bool:
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns(table_name)]
    return column_name in cols


def _safe_create_index(bind, name: str, table: str, cols: list[str], unique: bool = False) -> None:
    # CREATE INDEX IF NOT EXISTS is easiest/most robust on Postgres
    cols_sql = ", ".join(cols)
    unique_sql = "UNIQUE " if unique else ""
    op.execute(sa.text(f'CREATE {unique_sql}INDEX IF NOT EXISTS "{name}" ON "{table}" ({cols_sql})'))


def _safe_drop_index(name: str) -> None:
    op.execute(sa.text(f'DROP INDEX IF EXISTS "{name}"'))


def _safe_add_fk_constraint(table: str, name: str, local_cols: list[str], remote_table: str, remote_cols: list[str]) -> None:
    # No IF NOT EXISTS for ADD CONSTRAINT; do a DO $$ block to ignore duplicates
    local = ", ".join(local_cols)
    remote = ", ".join(remote_cols)
    op.execute(
        sa.text(
            f"""
DO $$
BEGIN
    ALTER TABLE "{table}"
    ADD CONSTRAINT "{name}"
    FOREIGN KEY ({local})
    REFERENCES "{remote_table}" ({remote})
    ON DELETE CASCADE;
EXCEPTION
    WHEN duplicate_object THEN
        NULL;
END $$;
"""
        )
    )


def _safe_drop_fk_constraint(table: str, name: str) -> None:
    op.execute(sa.text(f'ALTER TABLE "{table}" DROP CONSTRAINT IF EXISTS "{name}"'))


def upgrade() -> None:
    bind = op.get_bind()

    # ---------------------------------------------------------
    # 1) organizations.owner_id (+ index + FK)
    # ---------------------------------------------------------
    if not _has_column(bind, "organizations", "owner_id"):
        op.add_column("organizations", sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True))

    # backfill any existing orgs that might have NULL owner_id (pick oldest user)
    op.execute(
        sa.text(
            """
UPDATE organizations
SET owner_id = (
    SELECT id FROM users ORDER BY created_at ASC LIMIT 1
)
WHERE owner_id IS NULL;
"""
        )
    )

    # now enforce NOT NULL
    op.alter_column("organizations", "owner_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)

    _safe_create_index(bind, "ix_organizations_owner_id", "organizations", ["owner_id"], unique=False)
    _safe_add_fk_constraint(
        table="organizations",
        name="fk_organizations_owner_id_users",
        local_cols=["owner_id"],
        remote_table="users",
        remote_cols=["id"],
    )

    # ---------------------------------------------------------
    # 2) projects.organization_id (+ index + FK) + backfill
    # ---------------------------------------------------------
    if not _has_column(bind, "projects", "organization_id"):
        op.add_column("projects", sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True))

    # Create/find a "Personal" org per project owner and backfill projects.organization_id
    owners = bind.execute(sa.text("SELECT DISTINCT owner_id FROM projects")).fetchall()

    for (owner_id,) in owners:
        # find an org for this owner
        row = bind.execute(
            sa.text(
                """
SELECT id
FROM organizations
WHERE owner_id = :oid
ORDER BY created_at ASC
LIMIT 1
"""
            ),
            {"oid": owner_id},
        ).fetchone()

        if row:
            org_id = row[0]
        else:
            org_id = uuid4()
            slug = f"personal-{str(owner_id)[:8]}"
            bind.execute(
                sa.text(
                    """
INSERT INTO organizations (id, name, slug, owner_id, created_at)
VALUES (:id, :name, :slug, :owner_id, NOW())
"""
                ),
                {"id": org_id, "name": "Personal", "slug": slug, "owner_id": owner_id},
            )

        # backfill projects missing org
        bind.execute(
            sa.text(
                """
UPDATE projects
SET organization_id = :org_id
WHERE owner_id = :oid
  AND organization_id IS NULL
"""
            ),
            {"org_id": org_id, "oid": owner_id},
        )

    # If there were any projects with NULL still (shouldn't happen), fail loudly instead of silently setting NOT NULL
    remaining = bind.execute(sa.text("SELECT COUNT(*) FROM projects WHERE organization_id IS NULL")).scalar()
    if remaining and int(remaining) > 0:
        raise RuntimeError(
            f"Cannot set projects.organization_id NOT NULL; {remaining} rows are still NULL. "
            f"Check your data/backfill logic."
        )

    op.alter_column("projects", "organization_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)

    _safe_create_index(bind, "ix_projects_organization_id", "projects", ["organization_id"], unique=False)
    _safe_add_fk_constraint(
        table="projects",
        name="fk_projects_organization_id_organizations",
        local_cols=["organization_id"],
        remote_table="organizations",
        remote_cols=["id"],
    )


def downgrade() -> None:
    bind = op.get_bind()

    # drop FK + index + column on projects
    _safe_drop_fk_constraint("projects", "fk_projects_organization_id_organizations")
    _safe_drop_index("ix_projects_organization_id")
    if _has_column(bind, "projects", "organization_id"):
        op.drop_column("projects", "organization_id")

    # drop FK + index + column on organizations
    _safe_drop_fk_constraint("organizations", "fk_organizations_owner_id_users")
    _safe_drop_index("ix_organizations_owner_id")
    if _has_column(bind, "organizations", "owner_id"):
        op.drop_column("organizations", "owner_id")