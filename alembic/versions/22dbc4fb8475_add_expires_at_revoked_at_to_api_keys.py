"""add expires_at revoked_at to api_keys

Revision ID: 22dbc4fb8475
Revises: 525008e51b3c
Create Date: 2026-02-26 12:13:23.067661

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '22dbc4fb8475'
down_revision: Union[str, Sequence[str], None] = '525008e51b3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "api_keys",
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "api_keys",
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("api_keys", "revoked_at")
    op.drop_column("api_keys", "expires_at")