from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class ImageHistory(Base):
    __tablename__ = "imagehistory"
    id = Column(Integer, primary_key=True, index=True)
    usedCredit = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("accounts.id"))
    user = relationship("Account", back_populates="image_histories")
    model_id = Column(Integer, ForeignKey("generatemodelitem.id"))
    model = relationship("GenerateModelItem", back_populates="image_histories")
    image_id = Column(Integer, ForeignKey("createdimage.id"))
    image = relationship("CreatedImage", back_populates="image_histories") 