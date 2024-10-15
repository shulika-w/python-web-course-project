"""
Module of rates' schemas
"""

from datetime import datetime
from pydantic import BaseModel, Field, UUID4, ConfigDict, field_validator

from app.src.schemas.images import ImageDb


class RateModel(BaseModel):
    rate: int = Field(ge=1, le=5)


class RateResponse(RateModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4 | int
    image_id: UUID4 | int
    rate: int
    user_id: UUID4 | int
    created_at: datetime
    updated_at: datetime


class RateImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    image: ImageDb
    avg_rate: float | None

    @field_validator("avg_rate")
    def round_avg_rate(cls, v):
        if v:
            return round(v, 2)
        return None
