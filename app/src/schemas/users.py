"""
Module of users' schemas
"""


from datetime import datetime
from typing import List, Optional
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



class TagModel(BaseModel):
    name: str = Field(max_length=25)


class TagResponse(TagModel):
    id: int

    class Config:
        orm_mode = True


class NoteBase(BaseModel):
    title: str = Field(max_length=50)
    description: str = Field(max_length=150)


class NoteModel(NoteBase):
    tags: List[int]


class NoteUpdate(NoteModel):
    done: bool


class NoteStatusUpdate(BaseModel):
    done: bool


class NoteResponse(NoteBase):
    id: int
    created_at: datetime
    tags: List[TagResponse]

    class Config:
        orm_mode = True