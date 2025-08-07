from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.schemas.generatemodelitemimage import GenerateModelItemImageRead

class GenerateModelItemBase(BaseModel):
    name: str
    credit: int
    level: int
    sampler_name: Optional[str] = None
    cfg: Optional[int] = None
    steps: Optional[int] = None
    model: Optional[str] = None
    positive_prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    denoise: Optional[float] = None
    scheduler: Optional[str] = None
    lora: Optional[Dict[str, Any]] = None

class GenerateModelItemCreate(GenerateModelItemBase):
    image_id: Optional[int] = None
    priority: Optional[int] = None  # Gönderilmezse otomatik atanacak
    lora: Optional[Dict[str, Any]] = None

class GenerateModelItemUpdate(BaseModel):
    name: Optional[str] = None
    credit: Optional[int] = None
    level: Optional[int] = None
    priority: Optional[int] = None
    image_id: Optional[int] = None
    sampler_name: Optional[str] = None
    cfg: Optional[int] = None
    steps: Optional[int] = None
    model: Optional[str] = None
    positive_prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    denoise: Optional[float] = None
    scheduler: Optional[str] = None
    lora: Optional[Dict[str, Any]] = None

class GenerateModelItemRead(BaseModel):
    id: int
    name: str
    credit: int
    level: int
    priority: int  # Asla null olamaz
    image: Optional[GenerateModelItemImageRead] = None
    sampler_name: Optional[str] = None
    cfg: Optional[int] = None
    steps: Optional[int] = None
    model: Optional[str] = None
    positive_prompt: Optional[str] = None
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    denoise: Optional[float] = None
    scheduler: Optional[str] = None
    lora: Optional[Dict[str, Any]] = None
    class Config:
        from_attributes = True 