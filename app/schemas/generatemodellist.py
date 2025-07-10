from pydantic import BaseModel
from typing import Optional, List
from app.schemas.generatemodelitem import GenerateModelItemRead

class GenerateModelListBase(BaseModel):
    name: str
    item_ids: Optional[List[int]] = None

class GenerateModelListCreate(GenerateModelListBase):
    pass

class GenerateModelListRead(GenerateModelListBase):
    id: int
    items: Optional[List[GenerateModelItemRead]] = None
    class Config:
        from_attributes = True 