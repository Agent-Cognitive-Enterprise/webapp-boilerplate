import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field

from models.base_model import BaseModel


class EmailVerificationToken(BaseModel, table=True):
    __tablename__ = "email_verification_tokens"

    user_id: uuid.UUID = Field(nullable=False, index=True)
    token_hash: str = Field(max_length=128, unique=True, index=True, nullable=False)
    expires_at: datetime = Field(nullable=False)
    used: bool = Field(default=False, nullable=False)
    used_at: Optional[datetime] = Field(default=None, nullable=True)
    ip: Optional[str] = Field(max_length=64, default=None, nullable=True)
