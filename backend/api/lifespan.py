# /backend/api/lifespan.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)


# noinspection PyUnusedLocal
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup complete.")

    yield

    logger.info("Application shutdown complete.")
