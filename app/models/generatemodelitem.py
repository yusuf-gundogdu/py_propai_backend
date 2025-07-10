from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class GenerateModelItem(Base):
    __tablename__ = "generatemodelitem"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    credit = Column(Integer, nullable=False)
    level = Column(Integer, nullable=False)
    list_id = Column(Integer, ForeignKey("generatemodellist.id"))
    list = relationship("GenerateModelList", back_populates="items")
    image_id = Column(Integer)  # Resim referansı
    create_images = relationship("CreateImage", back_populates="model")
    created_images = relationship("CreatedImage", back_populates="model")
    image_histories = relationship("ImageHistory", back_populates="model") 