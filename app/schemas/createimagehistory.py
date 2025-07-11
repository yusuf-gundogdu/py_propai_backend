from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class GenerateModelItemImageRead(BaseModel):
    id: int
    fileName: str
    filePath: str
    fileSize: Optional[int] = None
    
    class Config:
        from_attributes = True

class GenerateModelItemRead(BaseModel):
    id: int
    name: str
    credit: int
    level: int
    priority: int
    image: Optional[GenerateModelItemImageRead] = None
    
    class Config:
        from_attributes = True

class CreateImageHistoryBase(BaseModel):
    udid: str
    model_id: int
    original_image_path: str
    original_file_name: Optional[str] = None
    original_file_size: Optional[int] = None

class CreateImageHistoryCreate(CreateImageHistoryBase):
    pass

class CreateImageHistoryUpdate(BaseModel):
    generated_image_path: Optional[str] = None
    generated_file_name: Optional[str] = None
    generated_file_size: Optional[int] = None
    status: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    processing_time_seconds: Optional[int] = None

class CreateImageHistoryRead(CreateImageHistoryBase):
    id: int
    generated_image_path: Optional[str] = None
    status: str
    credit: int
    level: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    processing_time_seconds: Optional[int] = None
    generated_file_name: Optional[str] = None
    generated_file_size: Optional[int] = None
    model: Optional[GenerateModelItemRead] = None
    
    class Config:
        from_attributes = True 