from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.models.base import Base

class GenerateModelItemImage(Base):
    __tablename__ = "generatemodelitemimage"
    id = Column(Integer, primary_key=True, index=True)
    fileName = Column(String, nullable=False)
    filePath = Column(String, nullable=False)
    fileSize = Column(Integer) 