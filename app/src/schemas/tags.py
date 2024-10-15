"""
Module of tags' schemas
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, UUID4, ConfigDict, StringConstraints
from pydantic import BaseModel, Field, UUID4, ConfigDict


class TagModel(BaseModel):
    title: Annotated[
        str,
        StringConstraints(
            min_length=2,
            max_length=49,
            strip_whitespace=True,
            pattern=r"^[a-zA-Z0-9_.-]+$",
        ),
    ] = Field()


class TagResponse(TagModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4 | int
    created_at: datetime
    updated_at: datetime
    user_id: UUID4 | int
