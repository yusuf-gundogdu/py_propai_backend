from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.database import get_db
from app.models.createimagehistory import CreateImageHistory
from app.models.account import Account
from app.models.generatemodelitem import GenerateModelItem
from app.schemas.createimagehistory import CreateImageHistoryUpdate
from typing import Optional
from datetime import datetime
import asyncio
import random
import os
import shutil
from uuid import uuid4

router = APIRouter(prefix="/generate", tags=["Generate"])

async def simulate_image_generation(history_id: int):
    """Simüle edilmiş resim generate işlemi"""
    
    # 10 saniye bekle
    await asyncio.sleep(10)
    
    # Yeni database session oluştur
    from app.database import engine
    async with engine.begin() as conn:
        # History kaydını al
        query = select(CreateImageHistory).where(CreateImageHistory.id == history_id)
        result = await conn.execute(query)
        history = result.scalar_one_or_none()
    
        if not history:
            print(f"History {history_id} bulunamadı")
            return
        
        # %80 başarılı, %20 başarısız (test amaçlı)
        is_success = random.random() < 0.8
        
        if is_success:
            # Başarılı senaryo
            generated_filename = f"ai_{uuid4()}.jpg"
            generated_path = f"/api/aigenerated/{generated_filename}"
            
            # AI generated klasörü (startup'ta oluşturuluyor)
            ai_generated_dir = "ai_generated"
            
            # Test amaçlı gerçek bir resim dosyası oluştur (gerçek uygulamada AI'dan gelecek)
            test_image_path = os.path.join(ai_generated_dir, generated_filename)
            file_size = 0
            
            try:
                # User uploads klasöründen rastgele bir resim kopyala
                user_uploads_dir = "user_uploads"
                if os.path.exists(user_uploads_dir):
                    user_images = [f for f in os.listdir(user_uploads_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
                    if user_images:
                        # Rastgele bir resim seç
                        random_image = random.choice(user_images)
                        source_path = os.path.join(user_uploads_dir, random_image)
                        
                        # Resmi kopyala
                        shutil.copy2(source_path, test_image_path)
                        file_size = os.path.getsize(test_image_path)
                        print(f"✅ AI resmi oluşturuldu: {test_image_path} (Kaynak: {random_image}, Boyut: {file_size} bytes)")
                    else:
                        # User uploads'ta resim yoksa placeholder oluştur
                        with open(test_image_path, "wb") as f:
                            # Daha büyük bir test resmi oluştur (100x100 pixel JPEG)
                            test_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00d\x00d\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
                            f.write(test_image_data)
                            file_size = len(test_image_data)
                        print(f"✅ AI resmi oluşturuldu: {test_image_path} (Placeholder, Boyut: {file_size} bytes)")
                else:
                    # User uploads klasörü yoksa placeholder oluştur
                    with open(test_image_path, "wb") as f:
                        test_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00d\x00d\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
                        f.write(test_image_data)
                        file_size = len(test_image_data)
                    print(f"✅ AI resmi oluşturuldu: {test_image_path} (Placeholder, Boyut: {file_size} bytes)")
            except Exception as e:
                print(f"❌ AI resmi oluşturulurken hata: {e}")
                # Hata durumunda başarısız olarak işaretle
                update_data = {
                    'status': 'failed',
                    'generated_image_path': None,
                    'generated_file_name': None,
                    'generated_file_size': None,
                    'completed_at': datetime.utcnow(),
                    'processing_time_seconds': 10,
                    'error_message': f'AI resmi oluşturulurken hata: {e}'
                }
                # Krediyi geri ver
                account_query = select(Account).where(Account.udid == history.udid)
                account_result = await conn.execute(account_query)
                account = account_result.scalar_one_or_none()
                
                if account:
                    account.credit += history.credit
                    print(f"❌ İşlem {history_id} başarısız oldu, {history.credit} kredi geri verildi")
                
                # History'yi güncelle ve return et
                for key, value in update_data.items():
                    setattr(history, key, value)
                await conn.commit()
                print(f"İşlem {history_id} tamamlandı: {update_data['status']}")
                return
            
            # Başarılı güncelleme
            update_data = {
                'status': 'success',
                'generated_image_path': generated_path,
                'generated_file_name': generated_filename,
                'generated_file_size': file_size,
                'completed_at': datetime.utcnow(),
                'processing_time_seconds': 10,
                'error_message': None
            }
            
            print(f"✅ İşlem {history_id} başarılı oldu")
            
        else:
            # Başarısız senaryo - krediyi geri ver
            update_data = {
                'status': 'failed',
                'generated_image_path': None,
                'generated_file_name': None,
                'generated_file_size': None,
                'completed_at': datetime.utcnow(),
                'processing_time_seconds': 10,
                'error_message': 'AI modeli resmi işlerken hata oluştu. Lütfen tekrar deneyin.'
            }
            
            # Krediyi geri ver
            account_query = select(Account).where(Account.udid == history.udid)
            account_result = await conn.execute(account_query)
            account = account_result.scalar_one_or_none()
            
            if account:
                account.credit += history.credit
                print(f"❌ İşlem {history_id} başarısız oldu, {history.credit} kredi geri verildi")
            else:
                print(f"❌ İşlem {history_id} başarısız oldu, hesap bulunamadı")
        
        # History'yi güncelle
        for key, value in update_data.items():
            setattr(history, key, value)
        
        await conn.commit()
        print(f"İşlem {history_id} tamamlandı: {update_data['status']}")

async def simulate_image_generation_simple(history_id: int, db: AsyncSession):
    """Basit simüle edilmiş resim generate işlemi"""
    
    # 5 saniye bekle
    await asyncio.sleep(5)
    
    # History kaydını al
    query = select(CreateImageHistory).where(CreateImageHistory.id == history_id)
    result = await db.execute(query)
    history = result.scalar_one_or_none()
    
    if not history:
        print(f"History {history_id} bulunamadı")
        return
    
    # Başarılı senaryo
    generated_filename = f"ai_{uuid4()}.jpg"
    generated_path = f"/api/aigenerated/{generated_filename}"
    
    # AI generated klasörü
    ai_generated_dir = "ai_generated"
    test_image_path = os.path.join(ai_generated_dir, generated_filename)
    file_size = 0
    
    try:
        # User uploads klasöründen rastgele bir resim kopyala
        user_uploads_dir = "user_uploads"
        if os.path.exists(user_uploads_dir):
            user_images = [f for f in os.listdir(user_uploads_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
            if user_images:
                random_image = random.choice(user_images)
                source_path = os.path.join(user_uploads_dir, random_image)
                shutil.copy2(source_path, test_image_path)
                file_size = os.path.getsize(test_image_path)
                print(f"✅ AI resmi oluşturuldu: {test_image_path} (Kaynak: {random_image}, Boyut: {file_size} bytes)")
            else:
                # Placeholder oluştur
                with open(test_image_path, "wb") as f:
                    test_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00d\x00d\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
                    f.write(test_image_data)
                    file_size = len(test_image_data)
                print(f"✅ AI resmi oluşturuldu: {test_image_path} (Placeholder, Boyut: {file_size} bytes)")
    except Exception as e:
        print(f"❌ AI resmi oluşturulurken hata: {e}")
        # Hata durumunda başarısız olarak işaretle
        update_data = {
            'status': 'failed',
            'generated_image_path': None,
            'generated_file_name': None,
            'generated_file_size': None,
            'completed_at': datetime.utcnow(),
            'processing_time_seconds': 5,
            'error_message': f'AI resmi oluşturulurken hata: {e}'
        }
        
        # History'yi güncelle
        for key, value in update_data.items():
            setattr(history, key, value)
        await db.commit()
        print(f"İşlem {history_id} tamamlandı: {update_data['status']}")
        return
    
    # Başarılı güncelleme
    update_data = {
        'status': 'success',
        'generated_image_path': generated_path,
        'generated_file_name': generated_filename,
        'generated_file_size': file_size,
        'completed_at': datetime.utcnow(),
        'processing_time_seconds': 5,
        'error_message': None
    }
    
    # History'yi güncelle
    for key, value in update_data.items():
        setattr(history, key, value)
    
    await db.commit()
    print(f"✅ İşlem {history_id} başarılı oldu: {update_data['status']}")

@router.post("/start/{history_id}")
async def start_generation(
    history_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Generate işlemini başlat"""
    
    # History kaydını kontrol et
    query = select(CreateImageHistory).where(CreateImageHistory.id == history_id)
    result = await db.execute(query)
    history = result.scalar_one_or_none()
    
    if not history:
        raise HTTPException(status_code=404, detail="History not found")
    
    if history.status != 'pending':
        raise HTTPException(status_code=400, detail="İşlem zaten başlatılmış")
    
    # Durumu processing'e çevir ve başlama zamanını kaydet
    history.status = 'processing'
    history.started_at = datetime.utcnow()
    await db.commit()
    
    # Direkt işlemi başlat (background task yerine)
    await simulate_image_generation_simple(history_id, db)
    
    return {"message": "Generate işlemi başlatıldı", "history_id": history_id}

@router.get("/status/{history_id}")
async def get_generation_status(
    history_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Generate işleminin durumunu kontrol et"""
    
    query = select(CreateImageHistory).options(
        joinedload(CreateImageHistory.model)
    ).where(CreateImageHistory.id == history_id)
    
    result = await db.execute(query)
    history = result.scalar_one_or_none()
    
    if not history:
        raise HTTPException(status_code=404, detail="History not found")
    
    return {
        "id": history.id,
        "status": history.status,
        "created_at": history.created_at,
        "started_at": history.started_at,
        "completed_at": history.completed_at,
        "processing_time_seconds": history.processing_time_seconds,
        "error_message": history.error_message,
        "credit": history.credit,
        "model": history.model.name if history.model else None
    } 