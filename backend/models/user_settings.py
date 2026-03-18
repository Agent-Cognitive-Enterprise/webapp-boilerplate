# /backend/models/user_settings.py

import uuid
from typing import Any, Dict
from sqlmodel import Column, Field, JSON, UniqueConstraint

from .base_model import BaseModel


class UserSettings(BaseModel, table=True):
    __tablename__ = "user_settings"
    __table_args__ = (UniqueConstraint("user_id", "route", name="uq_user_route"),)

    user_id: uuid.UUID = Field(nullable=False, index=True)
    route: str = Field(nullable=False, index=True)
    settings: Dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
