from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class CreateImage(Base):
    __tablename__ = "createimage"
    id = Column(Integer, primary_key=True, index=True)
    createImagePath = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("accounts.id"))
    user = relationship("Account", back_populates="create_images")
    model_id = Column(Integer, ForeignKey("generatemodelitem.id"))
    model = relationship("GenerateModelItem", back_populates="create_images") 