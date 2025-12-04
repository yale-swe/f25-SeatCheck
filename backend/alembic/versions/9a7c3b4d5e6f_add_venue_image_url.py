"""add venue image_url

Revision ID: 9a7c3b4d5e6f
Revises: f7e6027583d9
Create Date: 2025-12-03 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9a7c3b4d5e6f"
down_revision: str = "f7e6027583d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("venues", sa.Column("image_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("venues", "image_url")
