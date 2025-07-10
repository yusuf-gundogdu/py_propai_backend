from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.models.base import Base

class GenerateModelList(Base):
    __tablename__ = "generatemodellist"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    items = relationship("GenerateModelItem", back_populates="list") 