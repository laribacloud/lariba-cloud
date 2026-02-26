"""merge heads

Revision ID: b7265285c3d6
Revises: 746bab1bf344, ac623d506dc1
Create Date: 2026-02-26 18:31:11.964298

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7265285c3d6'
down_revision: Union[str, Sequence[str], None] = ('746bab1bf344', 'ac623d506dc1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
