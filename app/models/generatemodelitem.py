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
    create_image_histories = relationship("CreateImageHistory", back_populates="model") 