from app.database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)  # Buradaki String SQLAlchemy'den geliyor, doğru
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Role ilişkisi
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    role = relationship("Role", back_populates="users")