# /backend/models/token_data.py

from pydantic import BaseModel, EmailStr


class TokenData(BaseModel):
    email: EmailStr | None = None
