# /backend/utils/db.py
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import SQLModel

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

    async def _migrate_system_settings_columns(conn):
        result = await conn.exec_driver_sql("PRAGMA table_info(system_settings)")
        existing_columns = {row[1] for row in result.fetchall()}

        required_columns = {
            "openai_api_key": "TEXT",
            "deepseek_api_key": "TEXT",
            "site_logo": "TEXT",
            "background_image": "TEXT",
            "smtp_host": "TEXT",
            "smtp_port": "INTEGER",
            "smtp_username": "TEXT",
            "smtp_password": "TEXT",
            "smtp_from_email": "TEXT",
            "smtp_use_tls": "BOOLEAN DEFAULT 1",
        }
        for column_name, column_type in required_columns.items():
            if column_name in existing_columns:
                continue
            await conn.exec_driver_sql(
                f"ALTER TABLE system_settings ADD COLUMN {column_name} {column_type}"
            )

    async def _migrate_users_columns(conn):
        result = await conn.exec_driver_sql("PRAGMA table_info(users)")
        existing_columns = {row[1] for row in result.fetchall()}

        required_columns = {
            "email_verified": "BOOLEAN DEFAULT 1",
        }
        for column_name, column_type in required_columns.items():
            if column_name in existing_columns:
                continue
            await conn.exec_driver_sql(
                f"ALTER TABLE users ADD COLUMN {column_name} {column_type}"
            )

    async def init_db():
        """Initialize database schema (creates tables if they don't exist)."""
        async with async_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
            await _migrate_system_settings_columns(conn)
            await _migrate_users_columns(conn)
        logger.info("Database schema created successfully.")
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
