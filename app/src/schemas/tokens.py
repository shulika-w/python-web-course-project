"""
Module of tokens' schemas
"""


from pydantic import BaseModel


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPasswordSetModel(BaseModel):
    password_set_token: str