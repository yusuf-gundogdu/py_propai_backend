from pydantic import BaseModel
from typing import Optional

class CreatedImageBase(BaseModel):
    createImagePath: str
    createdImagePath: str
    credit: int
    Status: str
    user_id: Optional[int]
    model_id: Optional[int]

class CreatedImageCreate(CreatedImageBase):
    pass

class CreatedImageRead(CreatedImageBase):
    id: int
    class Config:
        from_attributes = True 