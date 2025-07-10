from sqlalchemy import Column, Integer, String, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import Base

class GenerateModelList(Base):
    __tablename__ = "generatemodellist"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    priority = Column(Integer, nullable=False, unique=True)  # Öncelik sırası, asla null olamaz
    item_ids = Column(JSON, nullable=True)  # generatemodelitem ID'lerini liste olarak tutar 