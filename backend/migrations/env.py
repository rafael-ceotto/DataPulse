import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings
from app.core.database import Base
from app.models.hospital import Hospital
from app.models.pipeline_run import PipelineRun
from app.models.infection import HospitalInfection
from app.models.insurance import HospitalEnrollment
from app.models.document_chunk import DocumentChunk
from app.models.insurance_br import HospitalInsuranceNetwork

settings = Settings()
config = context.config
config.set_main_option("sqlalchemy.url", settings.DB_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# These database objects exist but have no corresponding SQLAlchemy model/index
# declaration (hospitals_name_trgm and idx_hospitals_country are indexes created
# directly in the DB; document_chunks_embedding_idx is a pgvector index;
# my_first_dbt_model is a table owned by dbt). Without this filter, every
# --autogenerate proposes dropping them, since Alembic only knows about objects
# declared via SQLAlchemy models. If one of these is ever properly declared as
# a model/Index in the future, remove it from these sets.
_IGNORED_TABLES = {"my_first_dbt_model"}
_IGNORED_INDEXES = {"hospitals_name_trgm", "idx_hospitals_country", "document_chunks_embedding_idx"}


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name in _IGNORED_TABLES:
        return False
    if type_ == "index" and name in _IGNORED_INDEXES:
        return False
    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata, include_object=include_object)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(settings.DB_URL)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())