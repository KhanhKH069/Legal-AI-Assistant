"""Initial migration

Revision ID: 4daa9d37ccc8
Revises:
Create Date: 2026-05-19 09:59:04.060320

"""

from typing import Sequence, Union


revision: str = "4daa9d37ccc8"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
