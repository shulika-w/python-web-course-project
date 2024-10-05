"""
Module of users' schemas
"""


from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, HttpUrl, UUID4, ConfigDict


class UserModel(BaseModel):
    username: str = Field(min_length=2, max_length=254)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserRequestEmail(BaseModel):
    email: EmailStr


class UserPasswordSetModel(BaseModel):
    password: str = Field(min_length=8, max_length=72)


class UserDb(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4 | int
    username: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime
    avatar: HttpUrl
    role: str


class UserResponse(BaseModel):
    user: UserDb
    message: str = "User successfully created"