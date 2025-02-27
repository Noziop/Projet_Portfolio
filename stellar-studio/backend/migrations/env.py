# migrations/env.py
import os
import sys
from pathlib import Path
from logging.config import fileConfig

print("Starting env.py...")

# Ajoute le répertoire backend au PYTHONPATH
backend_path = Path(__file__).parents[1].absolute()
sys.path.insert(0, str(backend_path))
print(f"Added to PYTHONPATH: {backend_path}")

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context


print("Importing models...")
try:
    # Import des modèles dans l'ordre
    from app.db.base_class import Base
    print("Models imported successfully!")
    print(f"Tables in metadata: {Base.metadata.tables.keys()}")
except Exception as e:
    print(f"Error importing models: {e}")

def get_url():
    return "mysql+mysqlconnector://stellaruser:stellarpassword@database:3306/stellarstudio"

config = context.config

print("Setting target_metadata...")
target_metadata = Base.metadata
print(f"Tables in target_metadata: {target_metadata.tables.keys()}")

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
