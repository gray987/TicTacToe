from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.enums import ErrorCode


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("created_at", check_fields=False)
    @classmethod
    def _created_at_is_utc(cls, value: datetime) -> datetime:
        """SQLite returns naive datetimes; they are UTC by construction."""
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class ErrorResponse(BaseModel):
    code: ErrorCode
    detail: str
