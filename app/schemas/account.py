from pydantic import BaseModel
from typing import Optional
from app.models.account import PlatformEnum

class AccountBase(BaseModel):
    udid: str
    platform: Optional[PlatformEnum]
    credit: Optional[int]
    level: Optional[int]

class AccountRead(BaseModel):
    id: int
    udid: str
    platform: PlatformEnum
    level: int
    credit: int
    timestamp: Optional[int] = None
    class Config:
        from_attributes = True

class AccountUpdate(BaseModel):
    udid: Optional[str] = None
    platform: Optional[PlatformEnum] = None
    level: Optional[int] = None
    credit: Optional[int] = None
    timestamp: Optional[int] = None 