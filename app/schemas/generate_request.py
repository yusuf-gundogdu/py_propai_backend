from pydantic import BaseModel
from typing import Optional

class GenerateRequestCreate(BaseModel):
    """Generate isteği oluşturma"""
    model_id: int
    udid: str

class GenerateRequestResponse(BaseModel):
    """Generate isteği cevabı"""
    generate_id: str
    message: str
    status: str
    
class GenerateStartResponse(BaseModel):
    """Generate başlatma cevabı"""
    history_id: int
    message: str
    status: str
    
class GenerateStatusResponse(BaseModel):
    """Generate durum kontrolü"""
    history_id: int
    status: str
    message: Optional[str] = None
    generated_image_path: Optional[str] = None
    processing_time_seconds: Optional[int] = None
    error_message: Optional[str] = None

class CreateImageHistory(BaseModel):
    """Create Image History"""
    generate_id: str
    model_id: int
    udid: str
    status: str
    message: Optional[str] = None
    generated_image_path: Optional[str] = None
    processing_time_seconds: Optional[int] = None
    error_message: Optional[str] = None
