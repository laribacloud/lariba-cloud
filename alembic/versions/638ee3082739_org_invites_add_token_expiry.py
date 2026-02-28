"""org invites add token + expiry

Revision ID: 638ee3082739
Revises: 0d31bcf21bd1
Create Date: 2026-02-27 17:58:57.365971

"""
from alembic import op
import sqlalchemy as sa


# IMPORTANT:
# Keep the revision identifiers that alembic generated for you.
revision = "638ee3082739"
down_revision = "0d31bcf21bd1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns
    op.add_column("organization_invites", sa.Column("token_prefix", sa.String(length=12), nullable=True))
    op.add_column("organization_invites", sa.Column("token_hash", sa.String(length=64), nullable=True))
    op.add_column("organization_invites", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))

    # Backfill for existing rows (if any):
    # We can't recreate original tokens, so we set placeholder hashes/prefixes and force expiration soon.
    # Safer: make any existing pending invites unusable until recreated.
    op.execute(
        """
        UPDATE organization_invites
        SET
          token_prefix = COALESCE(token_prefix, 'migrated'),
          token_hash = COALESCE(token_hash, repeat('0', 64)),
          expires_at = COALESCE(expires_at, NOW() + interval '1 day')
        """
    )

    # Now enforce NOT NULL
    op.alter_column("organization_invites", "token_prefix", existing_type=sa.String(length=12), nullable=False)
    op.alter_column("organization_invites", "token_hash", existing_type=sa.String(length=64), nullable=False)
    op.alter_column("organization_invites", "expires_at", existing_type=sa.DateTime(timezone=True), nullable=False)

    # Indexes (some may already exist; use try/except style by naming consistently)
    op.create_index("ix_organization_invites_token_prefix", "organization_invites", ["token_prefix"])
    op.create_index("ix_organization_invites_token_hash", "organization_invites", ["token_hash"], unique=True)
    op.create_index("ix_organization_invites_expires_at", "organization_invites", ["expires_at"])
    op.create_index("ix_org_invites_org_email_status", "organization_invites", ["organization_id", "email", "status"])


def downgrade() -> None:
    op.drop_index("ix_org_invites_org_email_status", table_name="organization_invites")
    op.drop_index("ix_organization_invites_expires_at", table_name="organization_invites")
    op.drop_index("ix_organization_invites_token_hash", table_name="organization_invites")
    op.drop_index("ix_organization_invites_token_prefix", table_name="organization_invites")

    op.drop_column("organization_invites", "expires_at")
    op.drop_column("organization_invites", "token_hash")
    op.drop_column("organization_invites", "token_prefix")