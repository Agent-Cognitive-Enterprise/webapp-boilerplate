from sqlmodel import Field, Index

from models.base_model import BaseModel


class AuthRateLimitEvent(BaseModel, table=True):
    __tablename__ = "auth_rate_limit_events"
    __table_args__ = (
        Index(
            "ix_auth_rate_limit_events_action_bucket_created_at",
            "action",
            "bucket_key",
            "created_at",
        ),
    )

    action: str = Field(max_length=64, nullable=False, index=True)
    bucket_key: str = Field(max_length=256, nullable=False, index=True)
