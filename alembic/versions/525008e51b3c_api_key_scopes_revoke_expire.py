"""api key scopes revoke expire

Revision ID: 525008e51b3c
Revises: eb47b4526faf
Create Date: 2026-02-26 10:43:04.988166
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "525008e51b3c"
down_revision: Union[str, Sequence[str], None] = "eb47b4526faf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Add scope as nullable first (so existing rows won't violate NOT NULL)
    op.add_column("api_keys", sa.Column("scope", sa.String(), nullable=True))

    # 2) Backfill existing rows
    op.execute("UPDATE api_keys SET scope = 'default' WHERE scope IS NULL")

    # 3) Make it NOT NULL going forward
    op.alter_column("api_keys", "scope", existing_type=sa.String(), nullable=False)

    # Keep revoked_at as-is
    op.add_column("api_keys", sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("api_keys", "revoked_at")
    op.drop_column("api_keys", "scope")
