"""
Module of comments' schemas
"""

from datetime import datetime
from pydantic import BaseModel, Field, UUID4, ConfigDict


class CommentModel(BaseModel):
    text: str = Field(min_length=2, max_length=2048)


class CommentResponse(CommentModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4 | int
    image_id: UUID4 | int
    text: str
    user_id: UUID4 | int
    parent_id: UUID4 | None = None
    created_at: datetime
    updated_at: datetime