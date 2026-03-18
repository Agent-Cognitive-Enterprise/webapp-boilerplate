# /backend/utils/db.py
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from settings import DB_TYPE, SQLITE_DB_PATH

logger = logging.getLogger(__name__)

# Use SQLite for both production and testing
# For testing, use an in-memory database via environment variable
if DB_TYPE == "sqlite":
    DATABASE_URL = f"sqlite+aiosqlite:///{SQLITE_DB_PATH}"
    async_engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        connect_args={
            "check_same_thread": False,
        },
    )
    logger.info(f"Using SQLite database: {DATABASE_URL}")
else:
    raise ValueError(f"Unsupported DB_TYPE: {DB_TYPE}. Only 'sqlite' is supported.")

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
