"""
Module of tags' schemas
"""
from datetime import datetime
from pydantic import BaseModel, Field, UUID4, ConfigDict


class TagModel(BaseModel):
    title: str = Field(min_length=2, max_length=25, pattern=r"^[^#]*$")


class TagResponse(TagModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID4 | int
    created_at: datetime
    user_id: UUID4 | int