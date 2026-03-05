# /backend/models/ui_label.py

from sqlmodel import Field

from models.base_model import BaseModel


class UiLabel(BaseModel, table=True):
    __tablename__ = "ui_labels"

    # "login.button", "profile.name.label", etc.
    key: str = Field(nullable=False, index=True)

    # "en", "de", "fr", "ru", etc.
    locale: str = Field(nullable=False, index=True)

    # Human or LLM-generated text
    value: str = Field(nullable=False)
