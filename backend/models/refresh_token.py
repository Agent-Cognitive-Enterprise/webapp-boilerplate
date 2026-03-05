# /backend/models/refresh_token.py

import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import Field

from models.base_model import BaseModel


class RefreshToken(BaseModel, table=True):
    __tablename__ = "refresh_tokens"

    user_id: uuid.UUID = Field(nullable=False, index=True)
    token_hash: str = Field(max_length=128, unique=True, index=True, nullable=False)
    expires_at: datetime = Field(nullable=False)
    revoked: bool = Field(default=False, nullable=False)
    rotated_from_id: Optional[uuid.UUID] = Field(
        default=None, nullable=True
    )  # It is an id of a previously issued token for the same user
    used_at: Optional[datetime] = Field(default=None, nullable=True)
    user_agent: Optional[str] = Field(max_length=256, default=None, nullable=True)
    ip: Optional[str] = Field(max_length=64, default=None, nullable=True)
