from pydantic import BaseModel

class DistrictBase(BaseModel):
    name: str
    city_id: int

class DistrictCreate(DistrictBase):
    pass

class DistrictUpdate(BaseModel):
    name: str | None = None
    city_id: int | None = None

class DistrictResponse(DistrictBase):
    id: int
    
    class Config:
        from_attributes = True