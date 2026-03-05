# /backend/models/ui_label_suggestion.py

import uuid
from sqlmodel import Field

from models.base_model import BaseModel


class UiLabelSuggestion(BaseModel, table=True):
    __tablename__ = "ui_label_suggestions"

    label_id: uuid.UUID = Field(nullable=False, index=True)
    user_id: uuid.UUID = Field(nullable=False, index=True) # User who suggested it

    value: str = Field(nullable=False)
