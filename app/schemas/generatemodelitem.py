from pydantic import BaseModel
from typing import Optional

class GenerateModelItemBase(BaseModel):
    name: str
    credit: int
    level: int
    list_id: Optional[int]
    image_id: Optional[int]

class GenerateModelItemCreate(GenerateModelItemBase):
    pass

class GenerateModelItemRead(GenerateModelItemBase):
    id: int
    class Config:
        from_attributes = True 