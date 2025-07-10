from pydantic import BaseModel
from typing import Optional, List
from app.schemas.generatemodelitem import GenerateModelItemRead

class GenerateModelListBase(BaseModel):
    name: str
    item_ids: Optional[List[int]] = None

class GenerateModelListCreate(GenerateModelListBase):
    priority: Optional[int] = None  # Gönderilmezse otomatik atanacak

class GenerateModelListUpdate(BaseModel):
    name: Optional[str] = None
    item_ids: Optional[List[int]] = None
    priority: Optional[int] = None

class GenerateModelListRead(GenerateModelListBase):
    id: int
    priority: int  # Asla null olamaz
    items: Optional[List[GenerateModelItemRead]] = None
    class Config:
        from_attributes = True 