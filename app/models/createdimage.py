from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class CreatedImage(Base):
    __tablename__ = "createdimage"
    id = Column(Integer, primary_key=True, index=True)
    createImagePath = Column(String, nullable=False)
    createdImagePath = Column(String, nullable=False)
    credit = Column(Integer, nullable=False)
    Status = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("accounts.id"))
    user = relationship("Account", back_populates="created_images")
    model_id = Column(Integer, ForeignKey("generatemodelitem.id"))
    model = relationship("GenerateModelItem", back_populates="created_images")
    image_histories = relationship("ImageHistory", back_populates="image") 