"""add ratings table

Revision ID: f7e6027583d9
Revises: 0001_core
Create Date: 2025-11-06 05:02:56.052522

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f7e6027583d9"
down_revision: str = "65bc8518c436"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ratings",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "venue_id",
            sa.Integer,
            sa.ForeignKey("venues.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("occupancy", sa.Integer, nullable=False),  # 0–5
        sa.Column("noise", sa.Integer, nullable=False),  # 0–5
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_ratings_venue_created", "ratings", ["venue_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_ratings_venue_created", table_name="ratings")
    op.drop_table("ratings")
