# /backend/utils/db.py
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from settings import DATABASE_URL, DB_TYPE, SQLITE_DB_PATH
from utils.db_config import resolve_database_config

logger = logging.getLogger(__name__)

db_config = resolve_database_config(
    database_url=DATABASE_URL,
    db_type=DB_TYPE,
    sqlite_db_path=SQLITE_DB_PATH,
)

engine_kwargs: dict = {"echo": False}
if db_config.dialect == "sqlite":
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_pre_ping"] = True

async_engine = create_async_engine(
    db_config.async_url,
    **engine_kwargs,
)

logger.info("Using %s database backend", db_config.dialect)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
