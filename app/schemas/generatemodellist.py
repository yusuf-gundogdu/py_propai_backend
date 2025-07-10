from pydantic import BaseModel
from typing import Optional

class GenerateModelListBase(BaseModel):
    name: str

class GenerateModelListCreate(GenerateModelListBase):
    pass

class GenerateModelListRead(GenerateModelListBase):
    id: int
    class Config:
        from_attributes = True 