"""
Module of users' schemas
"""

from dataclasses import dataclass
from datetime import datetime, date
from pydantic import (
    BaseModel,
    Field,
    EmailStr,
    HttpUrl,
    UUID4,
    ConfigDict,
)
from typing import Annotated

from fastapi import Form

from app.src.database.models import Role


class UserModel(BaseModel):
    username: str = Field(min_length=2, max_length=254)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    first_name: Annotated[str | None, Field(max_length=254)]
    last_name: Annotated[str | None, Field(max_length=254)]
    phone: Annotated[str | None, Field(max_length=38)]
    birthday: date | None


@dataclass
class UserCreateForm:
    username: str = Form(...)
    email: str = Form(...)
    password: str = Form(...)
    first_name: Annotated[str | None, Form(...)] = None
    last_name: Annotated[str | None, Form(...)] = None
    phone: Annotated[str | None, Form(...)] = None
    birthday: Annotated[str | None, Form(...)] = None


class UserUpdateModel(BaseModel):
    first_name: Annotated[str | None, Field(max_length=254)]
    last_name: Annotated[str | None, Field(max_length=254)]
    phone: Annotated[str | None, Field(max_length=38)]
    birthday: date | None


@dataclass
class UserUpdateForm:
    first_name: Annotated[str | None, Form(...)] = None
    last_name: Annotated[str | None, Form(...)] = None
    phone: Annotated[str | None, Form(...)] = None
    birthday: Annotated[str | None, Form(...)] = None


class UserRequestEmail(BaseModel):
    email: EmailStr


class UserPasswordSetModel(BaseModel):
    password: str = Field(min_length=8, max_length=72)


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
