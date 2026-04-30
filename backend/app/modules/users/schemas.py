from pydantic import BaseModel, ConfigDict
from typing import Optional


class UserCreate(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


class UserAuthenticate(BaseModel):
    username: str
    password: str


class UserToken(BaseModel):
    access_token: str
    token_type: str