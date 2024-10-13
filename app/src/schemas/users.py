"""
Module of users' schemas
"""


from datetime import datetime, date
from pydantic import BaseModel, Field, EmailStr, HttpUrl, UUID4, ConfigDict, validator


def date_validator(birthday):
    if len(birthday) == 0:
        return None
    birthday = datetime.strptime(birthday, "%Y-%m-%d").date()
    return birthday


class UserModel(BaseModel):
    username: str = Field(min_length=2, max_length=254)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    first_name: str = Field(max_length=254)
    last_name: str = Field(max_length=254)
    phone: str = Field(max_length=38)
    birthday: date | str

    _date_validator = validator("birthday", allow_reuse=True)(date_validator)


class UserRequestEmail(BaseModel):
    email: EmailStr


class UserPasswordSetModel(BaseModel):
    password: str = Field(min_length=8, max_length=72)


class UserDb(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4 | int
    username: str
    email: EmailStr
    first_name: str = Field(max_length=254)
    last_name: str = Field(max_length=254)
    phone: str = Field(max_length=38)
    birthday: date | None
    created_at: datetime
    updated_at: datetime
    avatar: HttpUrl
    role: str
    is_active: bool


class UserResponse(BaseModel):
    user: UserDb
    message: str = "User successfully created"