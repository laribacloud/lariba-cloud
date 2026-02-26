"""merge heads

Revision ID: 156229ad3897
Revises: 34ad027de4ff
Create Date: 2026-02-26 23:35:47.628940

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '156229ad3897'
down_revision: Union[str, Sequence[str], None] = '34ad027de4ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
