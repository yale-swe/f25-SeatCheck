# backend/alembic/env.py
from __future__ import annotations

from logging.config import fileConfig
import sys
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# --- Ensure backend/src is on sys.path so "import app" works ---
HERE = Path(__file__).resolve()
BACKEND = HERE.parents[1]  # .../backend
SRC_DIR = BACKEND / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# --- Now imports from your app are possible ---
from app.database import Base  # ONE Base for all models  # noqa: E402
from app.config import settings  # your Pydantic settings  # noqa: E402

# Alembic Config object (reads alembic.ini)
config = context.config

# If you prefer settings to drive the URL (recommended), set it here:
config.set_main_option("sqlalchemy.url", settings.database_url)

# Configure logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live engine."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a live engine/connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
