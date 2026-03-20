from typing import Any

from pydantic import BaseModel


class UILabelRequest(BaseModel):
    action: str
    locale: str | None = None
    values_hash: str | None = None
    key: str | None = None
    value: str | None = None


class UILabelResponse(BaseModel):
    success: bool
    data: Any | None = None
    message: str | None = None
