from pydantic import BaseModel
from typing import Optional

class CityBase(BaseModel):
    name: str

class CityCreate(CityBase):
    pass

class CityUpdate(BaseModel):  # Bu satırı ekleyin
    name: Optional[str] = None

class CityResponse(CityBase):
    id: int
    
    class Config:
        from_attributes = True