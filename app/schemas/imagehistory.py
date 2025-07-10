from pydantic import BaseModel
from typing import Optional

class ImageHistoryBase(BaseModel):
    usedCredit: int
    user_id: Optional[int]
    model_id: Optional[int]
    image_id: Optional[int]

class ImageHistoryCreate(ImageHistoryBase):
    pass

class ImageHistoryRead(ImageHistoryBase):
    id: int
    class Config:
        from_attributes = True 