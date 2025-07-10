from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class District(Base):
    __tablename__ = "districts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    city_id = Column(Integer, ForeignKey("city.id"), nullable=False)
    
    city = relationship("City", back_populates="districts")