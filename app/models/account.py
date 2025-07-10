import enum
from sqlalchemy import Column, Integer, String, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base

class PlatformEnum(enum.Enum):
    ANDROID = "ANDROID"
    IOS = "IOS"

class Account(Base):
    __tablename__ = "account"
    __table_args__ = (UniqueConstraint("udid", "platform", name="uix_udid_platform"),)
    id = Column(Integer, primary_key=True, index=True)
    udid = Column(String, nullable=False)
    platform = Column(Enum(PlatformEnum), nullable=False)
    credit = Column(Integer)
    level = Column(Integer)
    timestamp = Column(Integer, nullable=True)
    create_images = relationship("CreateImage", back_populates="user")
    created_images = relationship("CreatedImage", back_populates="user")
    image_histories = relationship("ImageHistory", back_populates="user") 