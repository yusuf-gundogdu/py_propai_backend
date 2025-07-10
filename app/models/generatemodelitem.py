from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base

class GenerateModelItem(Base):
    __tablename__ = "generatemodelitem"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)  # İsim unique olmalı
    credit = Column(Integer, nullable=False)
    level = Column(Integer, nullable=False)
    priority = Column(Integer, nullable=False, unique=True)  # Öncelik sırası, asla null olamaz
    image_id = Column(Integer, ForeignKey("generatemodelitemimage.id"))  # Tek bir resim ID'si
    image = relationship("GenerateModelItemImage")
    create_images = relationship("CreateImage", back_populates="model")
    created_images = relationship("CreatedImage", back_populates="model")
    image_histories = relationship("ImageHistory", back_populates="model") 