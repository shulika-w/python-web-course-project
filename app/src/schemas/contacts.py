"""
Module of contacts' schemas
"""


from datetime import datetime, date
from pydantic import BaseModel, Field, EmailStr, UUID4, ConfigDict


class ContactModel(BaseModel):
    first_name: str = Field(min_length=2, max_length=254)
    last_name: str = Field(min_length=2, max_length=254)
    email: EmailStr
    phone: str = Field(max_length=38)
    birthday: date
    address: str = Field(max_length=254)


class ContactResponse(ContactModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID4 | int
    created_at: datetime
    updated_at: datetime
    user_id: UUID4 | int