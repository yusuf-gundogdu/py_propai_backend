from pydantic import BaseModel
from typing import Optional

class CreateImageBase(BaseModel):
    createImagePath: str
    user_id: Optional[int]
    model_id: Optional[int]

class CreateImageCreate(CreateImageBase):
    pass

class CreateImageRead(CreateImageBase):
    id: int
    class Config:
        from_attributes = True 