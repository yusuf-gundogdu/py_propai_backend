import enum
from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship
from app.models.base import Base

class PlatformEnum(enum.Enum):
    ANDROID = "ANDROID"
    IOS = "IOS"

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    udid = Column(String, unique=True, nullable=False)
    platform = Column(Enum(PlatformEnum), nullable=True)
    credit = Column(Integer)
    level = Column(Integer)
    create_images = relationship("CreateImage", back_populates="user")
    created_images = relationship("CreatedImage", back_populates="user")
    image_histories = relationship("ImageHistory", back_populates="user") 