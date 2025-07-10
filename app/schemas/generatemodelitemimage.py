from pydantic import BaseModel
from typing import Optional

class GenerateModelItemImageBase(BaseModel):
    fileName: str
    filePath: str
    fileSize: Optional[int]

class GenerateModelItemImageCreate(GenerateModelItemImageBase):
    pass

class GenerateModelItemImageRead(GenerateModelItemImageBase):
    id: int
    class Config:
        from_attributes = True 