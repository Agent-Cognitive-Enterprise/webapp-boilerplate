# /backend/models/ui_label.py

from sqlmodel import Field

from models.base_model import BaseModel


class UiLocale(BaseModel, table=True):
    __tablename__ = "ui_locales"

    # "en", "de", "fr", "ru", etc.
    locale: str = Field(nullable=False, index=True)

    # Hash of an alphabetically sorted list of values
    values_hash: str = Field(nullable=False)
