# /backend/models/base_model.py

import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import func


class BaseModel(SQLModel, table=False):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False
    )
    created_at: Optional[datetime] = Field(
        sa_column_kwargs={"server_default": func.now()},
        nullable=False,
    )
    updated_at: Optional[datetime] = Field(
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()},
        nullable=False,
    )
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)
