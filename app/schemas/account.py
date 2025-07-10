from pydantic import BaseModel
from typing import Optional

class AccountBase(BaseModel):
    name: str
    city_id: int
    district_id: int

class AccountCreate(AccountBase):
    pass

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    city_id: Optional[int] = None
    district_id: Optional[int] = None

class AccountResponse(AccountBase):
    id: int
    
    class Config:
        from_attributes = True