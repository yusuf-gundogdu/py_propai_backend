from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base

class CreateImageHistory(Base):
    __tablename__ = "create_image_history"
    
    id = Column(Integer, primary_key=True, index=True)
    udid = Column(String(255), nullable=False)
    model_id = Column(Integer, ForeignKey("generatemodelitem.id"), nullable=False)
    
    # Resim Yolları
    original_image_path = Column(String(500), nullable=False)  # Kullanıcının yüklediği resim
    generated_image_path = Column(String(500))  # AI'ın oluşturduğu resim (başarılı olursa)
    
    # Kredi ve Seviye
    credit = Column(Integer, nullable=False, default=0)  # Harcanan kredi miktarı
    level = Column(Integer, nullable=False)  # Kullanıcının seviyesi (0=ücretsiz, 1,2,3,4=ücretli)
    
    # Durum Yönetimi
    status = Column(String(20), nullable=False, default='pending')  # 'pending', 'processing', 'success', 'failed', 'cancelled'
    
    # Zaman Damgaları
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True))  # İşlem başlama zamanı
    completed_at = Column(DateTime(timezone=True))  # İşlem bitiş zamanı
    
    # Hata ve Detaylar
    error_message = Column(Text)  # Hata mesajı (varsa)
    processing_time_seconds = Column(Integer)  # İşlem süresi (saniye)
    
    # Metadata
    original_file_size = Column(Integer)  # Orijinal dosya boyutu (bytes)
    generated_file_size = Column(Integer)  # Oluşturulan dosya boyutu (bytes)
    original_file_name = Column(String(255))  # Orijinal dosya adı
    generated_file_name = Column(String(255))  # Oluşturulan dosya adı
    
    # İlişkiler
    model = relationship("GenerateModelItem", back_populates="create_image_histories") 