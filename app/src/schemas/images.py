"""
Module of images' schemas
"""

from datetime import datetime
from enum import Enum
import json
from typing import Annotated, List

from fastapi import UploadFile, File
from pydantic import (
    BaseModel,
    HttpUrl,
    UUID4,
    ConfigDict,
    conlist,
    field_validator,
)
from app.src.schemas.tags import TagModel, TagResponse
from app.src.utils.as_form import as_form

MAX_NUMBER_OF_TAGS_PER_IMAGE = 5


@as_form
class ImageModel(BaseModel):
    file: Annotated[UploadFile, File()]
    description: str | None = None
    tags: conlist(str, max_length=MAX_NUMBER_OF_TAGS_PER_IMAGE) = []

    @field_validator("tags", mode="before")
    def check_tags_before(cls, v):
        if not v[0]:
            return []
        v = list(set(v[0].split(",")))
        tags = []
        for tag_title in v:
            TagModel.model_validate({"title": tag_title})
            tags.append(tag_title)
        return tags

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_to_json

    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


class ImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4 | int
    url: HttpUrl
    user_id: UUID4 | int
    description: str | None
    created_at: datetime
    updated_at: datetime


class ImageDb(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4 | int
    url: HttpUrl
    user_id: UUID4 | int
    description: str | None
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse]


class ImageDescriptionModel(BaseModel):
    description: str | None


class CloudinaryTransformations(str, Enum):
    none = ""
    crop = "c_thumb,g_face,h_200,w_200,z_1/f_auto/r_max/"
    resize = "ar_1.0,c_fill,h_250"
    rotate = "a_10/"
    improve = "e_improve:outdoor:29/"
    brightness = "e_brightness:80/"
    blackwhite = "e_blackwhite:49/"
    saturation = "e_saturation:50/"
    border = "bo_10px_solid_lightblue/"
    rounded_corners = "r_100/"
