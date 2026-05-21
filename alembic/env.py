import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

# Cargar .env antes de importar los modelos
load_dotenv()

# Importar TODOS los modelos para que SQLModel registre sus tablas en metadata
import app.models  # noqa: F401

# Objeto de configuracion de Alembic (lee alembic.ini)
config = context.config

# Inyectar DATABASE_URL desde variable de entorno (no hardcodear credenciales)
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL no esta configurada en el archivo .env")
config.set_main_option("sqlalchemy.url", database_url)

# Configurar logging segun alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata objetivo: la de SQLModel (incluye todas las tablas declaradas)
target_metadata = SQLModel.metadata


# ── Migraciones offline (sin conexion activa) ─────────────────────────────────
def run_migrations_offline() -> None:
    """Genera SQL sin conectarse a la BD (util para revision previa)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Migraciones online (con conexion activa) ──────────────────────────────────
def run_migrations_online() -> None:
    """Aplica las migraciones directamente contra la BD."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
