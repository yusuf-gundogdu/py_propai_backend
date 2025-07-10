from pydantic import BaseModel
from typing import Optional
from app.schemas.generatemodelitemimage import GenerateModelItemImageRead

class GenerateModelItemBase(BaseModel):
    name: str
    credit: int
    level: int

class GenerateModelItemCreate(GenerateModelItemBase):
    image_id: Optional[int] = None
    priority: Optional[int] = None  # Gönderilmezse otomatik atanacak

class GenerateModelItemRead(BaseModel):
    id: int
    name: str
    credit: int
    level: int
    priority: int  # Asla null olamaz
    image: Optional[GenerateModelItemImageRead] = None
    class Config:
        from_attributes = True 