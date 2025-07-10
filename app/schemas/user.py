from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    username: str  # Just use str directly

class UserCreate(UserBase):
    password: str  # Just use str directly

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None