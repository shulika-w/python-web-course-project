"""
Module of users' schemas
"""

from datetime import datetime, date
import json
from pydantic import (
    BaseModel,
    Field,
    EmailStr,
    SecretStr,
    HttpUrl,
    UUID4,
    ConfigDict,
    SkipValidation,
    field_validator,
)
import re
from typing import Annotated

from fastapi import UploadFile

from app.src.database.models import Role
from app.src.utils.as_form import as_form


@as_form
class UserModel(BaseModel):
    username: str = Field(min_length=2, max_length=254)
    email: EmailStr
    password: SecretStr = Field(min_length=8, max_length=72)
    first_name: Annotated[str | None, Field(max_length=254)] = None
    last_name: Annotated[str | None, Field(max_length=254)] = None
    phone: Annotated[str | None, Field(max_length=38)] = None
    birthday: date | None = None
    avatar: Annotated[UploadFile, SkipValidation] = None

    @field_validator("username")
    def check_username(cls, v):
        if not re.match(r"(?i)^(?!me$).*", v):
            raise ValueError("username shouldn't be just 'me'")
        return v

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_to_json

    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


@as_form
class UserUpdateModel(BaseModel):
    first_name: Annotated[str | None, Field(max_length=254)] = None
    last_name: Annotated[str | None, Field(max_length=254)] = None
    phone: Annotated[str | None, Field(max_length=38)] = None
    birthday: date | None = None
    avatar: Annotated[UploadFile, SkipValidation] = None

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_to_json

    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


class UserSetRoleModel(BaseModel):
    role: Role


class UserDb(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4 | int
    username: str = Field(min_length=2, max_length=254)
    email: EmailStr
    first_name: Annotated[str | None, Field(max_length=254)]
    last_name: Annotated[str | None, Field(max_length=254)]
    phone: Annotated[str | None, Field(max_length=38)]
    birthday: date | None
    created_at: datetime
    updated_at: datetime
    avatar: HttpUrl
    role: Role
    is_active: bool


class UserResponse(BaseModel):
    user: UserDb
    message: str = "User successfully created"
