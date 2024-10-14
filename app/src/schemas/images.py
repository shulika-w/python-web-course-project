"""
Module of images' schemas
"""


from dataclasses import dataclass
from datetime import datetime
from typing import Annotated

from fastapi import Form
from pydantic import BaseModel, Field, UUID4, ConfigDict


class ImageModel(BaseModel):
    # user_id: UUID4 | int
    description: str | None


@dataclass
class ImageCreateForm:
    # user_id: UUID4 | int
    description: Annotated[str | None, Form(...)] = None


class ImageDb(BaseModel):
    id: UUID4 | int
    url: str
    user_id: UUID4 | int
    description: str | None
    created_at: datetime
    updated_at: datetime
    rates: int

    model_config = ConfigDict(from_attributes=True)