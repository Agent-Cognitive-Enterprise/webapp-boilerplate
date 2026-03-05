# /backend/schemas/user_settings.py

from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional
import uuid


class UserSettingsIn(BaseModel):
    route: str
    settings: Optional[Dict[str, Any]] = None


class UserSettingsOut(UserSettingsIn):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
