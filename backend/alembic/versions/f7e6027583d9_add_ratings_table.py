"""add ratings table

Revision ID: f7e6027583d9
Revises: 0001_core
Create Date: 2025-11-06 05:02:56.052522

"""

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f7e6027583d9"
down_revision: str = "65bc8518c436"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This migration previously attempted to create the `ratings` table, but
    # the core/base migration (0001_core) already creates that table. To
    # avoid duplicate-table errors when applying migrations to an existing
    # database, keep this migration focused on the additional index it was
    # meant to provide.
    op.create_index("ix_ratings_venue_created", "ratings", ["venue_id", "created_at"])


def downgrade() -> None:
    # Only drop the index created in upgrade(); do not attempt to drop the
    # `ratings` table here because it is owned by the base migration.
    op.drop_index("ix_ratings_venue_created", table_name="ratings")
