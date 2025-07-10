from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    city_id = Column(Integer, ForeignKey("city.id"))
    district_id = Column(Integer, ForeignKey("districts.id"))
    
    city = relationship("City")
    district = relationship("District")