# /backend/api/lifespan.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

from settings import DB_TYPE
from utils.db import init_db

logger = logging.getLogger(__name__)


# noinspection PyUnusedLocal
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database schema for SQLite
    if DB_TYPE == "sqlite":
        await init_db()
        logger.info("✅ Database initialized.")

    yield

    logger.info("Application shutdown complete.")
