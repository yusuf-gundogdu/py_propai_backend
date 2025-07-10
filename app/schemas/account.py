from pydantic import BaseModel
from typing import Optional
from app.models.account import PlatformEnum

class AccountBase(BaseModel):
    udid: str
    platform: Optional[PlatformEnum]
    credit: Optional[int]
    level: Optional[int]

class AccountCreate(AccountBase):
    pass

class AccountRead(AccountBase):
    id: int
    class Config:
        from_attributes = True 