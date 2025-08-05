from fastapi import Query, APIRouter, Depends, HTTPException, BackgroundTasks, status, UploadFile, File, Form
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.database import get_db
from app.models.createimagehistory import CreateImageHistory
from app.models.account import Account
from app.models.generatemodelitem import GenerateModelItem
from app.schemas.createimagehistory import CreateImageHistoryUpdate
from app.schemas.generate_request import GenerateRequestCreate, GenerateRequestResponse, GenerateStartResponse, GenerateStatusResponse
import asyncio
import random
import os
import shutil
from uuid import uuid4
from pydantic import BaseModel

router = APIRouter(prefix="/generate", tags=["Generate"])

@router.post("/request", response_model=GenerateRequestResponse)
async def request_generate(
    request: GenerateRequestCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    1. Aşama: Generate isteği kontrolü
    - Kullanıcının kredisini kontrol et
    - Kullanıcının level'ını model level'ı ile karşılaştır
    - Şartlar sağlanırsa unique generate_id döner
    """
    
    # Kullanıcının hesabını bul
    account_query = select(Account).where(Account.udid == request.udid)
    account_result = await db.execute(account_query)
    account = account_result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=404, 
            detail="Kullanıcı hesabı bulunamadı. Lütfen önce hesap oluşturun."
        )
    
    # Generate modelini bul
    model_query = select(GenerateModelItem).where(GenerateModelItem.id == request.model_id)
    model_result = await db.execute(model_query)
    model = model_result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(
            status_code=404,
            detail="Generate modeli bulunamadı."
        )
    
    # Kredi kontrolü
    if account.credit < model.credit:
        raise HTTPException(
            status_code=400,
            detail=f"Yetersiz kredi. Bu model için {model.credit} kredi gerekli, hesabınızda {account.credit} kredi var."
        )
    
    # Level kontrolü
    if account.level < model.level:
        # Kullanıcının level'ı model level'ından düşük
        if account.level == 0:
            # Ücretsiz kullanıcı, ücretli model
            raise HTTPException(
                status_code=403,
                detail=f"Bu model ücretli kullanıcılar içindir (Level {model.level} gerekli). Şu anda ücretsiz kullanıcısınız (Level {account.level}). Premium'a geçmek için uygulamayı güncelleyin."
            )
        else:
            # Ücretli kullanıcı ama level yetersiz
            raise HTTPException(
                status_code=403,
                detail=f"Bu model için Level {model.level} gerekli. Şu anda Level {account.level} kullanıcısısınız. Yüksek level'a geçmek için uygulamayı güncelleyin."
            )
    
    # Şartlar sağlandı, unique generate_id oluştur
    generate_id = str(uuid4())
    
    return GenerateRequestResponse(
        generate_id=generate_id,
        message=f"Generate isteği onaylandı. Model: {model.name}, Kredi: {model.credit}",
        status="approved"
    )


@router.post("/start", response_model=GenerateRequestResponse)
async def start_generate(
    request: GenerateRequestCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Kullanıcı sadece model_id ve udid gönderir. Tüm kontroller backend'de yapılır.
    Şartlar sağlanırsa unique generate_id döner, aksi durumda hata/exceptions döner.
    """
    # Kullanıcı hesabı kontrolü
    account_query = select(Account).where(Account.udid == request.udid)
    account_result = await db.execute(account_query)
    account = account_result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Kullanıcı hesabı bulunamadı.")

    # Model kontrolü
    model_query = select(GenerateModelItem).where(GenerateModelItem.id == request.model_id)
    model_result = await db.execute(model_query)
    model = model_result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model bulunamadı.")

    # Kredi kontrolü
    if account.credit < model.credit:
        raise HTTPException(status_code=400, detail=f"Yetersiz kredi. Model için {model.credit} kredi gerekli, hesabınızda {account.credit} kredi var.")

    # Level kontrolü
    if account.level < model.level:
        if account.level == 0:
            raise HTTPException(status_code=403, detail=f"Bu model ücretli kullanıcılar içindir (Level {model.level} gerekli). Şu anda ücretsiz kullanıcısınız.")
        else:
            raise HTTPException(status_code=403, detail=f"Bu model için Level {model.level} gerekli. Şu anda Level {account.level} kullanıcısısınız.")

    # Şartlar sağlandı, generate_id oluştur
    generate_id = str(uuid4())

    # History kaydı oluştur
    history = CreateImageHistory(
        udid=request.udid,
        model_id=request.model_id,
        generate_id=generate_id,
        original_image_path="",
        credit=model.credit,
        level=account.level,
        status='pending'
    )
    db.add(history)
    await db.commit()
    await db.refresh(history)

    return GenerateRequestResponse(
        generate_id=generate_id,
        message=f"Generate isteği onaylandı. Model: {model.name}, Kredi: {model.credit}",
        status="approved"
    )


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

async def simulate_image_generation_simple(history_id: int, original_db: AsyncSession):
    """Basit simüle edilmiş resim generate işlemi"""
    
    # 5 saniye bekle
    await asyncio.sleep(5)
    
    # Yeni database session oluştur (async task için)
    from app.database import async_session
    async with async_session() as db:
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

@router.get("/status/{history_id}", response_model=GenerateStatusResponse)
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
    status_messages = {
        'pending': 'İşlem beklemede',
        'processing': 'Resim generate ediliyor...',
        'success': 'Resim başarıyla oluşturuldu',
        'failed': 'İşlem başarısız oldu',
        'cancelled': 'İşlem iptal edildi'
    }
    return GenerateStatusResponse(
        history_id=history.id,
        status=history.status,
        message=status_messages.get(history.status, 'Bilinmeyen durum'),
        generated_image_path=history.generated_image_path,
        processing_time_seconds=history.processing_time_seconds,
        error_message=history.error_message
    )


@router.post("/upload/{generate_id}", response_model=GenerateStartResponse)
async def upload_image(
    generate_id: str,
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Kullanıcı sadece generate_id ve image gönderir. Diğer tüm bilgiler backend'de bulunur.
    """
    # History kaydını bul
    from sqlalchemy.future import select
    history_query = select(CreateImageHistory).where(CreateImageHistory.generate_id == generate_id)
    result = await db.execute(history_query)
    history = result.scalar_one_or_none()
    if not history:
        raise HTTPException(status_code=404, detail="Geçersiz generate_id.")

    # Resim dosyası kontrolü
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Sadece resim dosyaları kabul edilir.")

    # Resmi kaydet
    try:
        file_extension = os.path.splitext(image.filename)[1] if image.filename else ".jpg"
        unique_filename = f"user_{generate_id}{file_extension}"
        file_path = os.path.join("user_uploads", unique_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        file_size = os.path.getsize(file_path)
        # Kredi düşümü: sadece resim başarıyla kaydedilirse
        # Account'u bul
        account_query = select(Account).where(Account.udid == history.udid)
        account_result = await db.execute(account_query)
        account = account_result.scalar_one_or_none()
        if account:
            # Model kredi miktarını bul
            model_query = select(GenerateModelItem).where(GenerateModelItem.id == history.model_id)
            model_result = await db.execute(model_query)
            model = model_result.scalar_one_or_none()
            if model and account.credit >= model.credit:
                account.credit -= model.credit
                await db.commit()
                await db.refresh(account)
                print(f"✅ Kullanıcı {account.udid} için {model.credit} kredi düşüldü. Yeni kredi: {account.credit}")
            else:
                print(f"❌ Kredi düşümü başarısız: model veya kredi yetersiz.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resim kaydedilirken hata oluştu: {str(e)}")

    # History kaydını güncelle
    history.original_image_path = f"/api/userupload/{unique_filename}"
    history.original_file_size = file_size
    history.original_file_name = image.filename
    history.status = 'processing'
    history.started_at = datetime.utcnow()
    await db.commit()
    await db.refresh(history)

    # Generate işlemini başlat (background'da)
    from app.routers.generate import simulate_image_generation_simple
    from app.websocket_server import ws_manager
    import asyncio
    
    # WebSocket'e bağlı generate makinası varsa ona gönder
    authenticated_clients = ws_manager.get_authenticated_clients()
    if authenticated_clients:
        # İlk authenticate edilmiş client'a gönder
        client_id = authenticated_clients[0]
        generate_request = {
            "history_id": history.id,
            "generate_id": generate_id,
            "original_image_path": history.original_image_path,
            "model_id": history.model_id,
            "udid": history.udid,
            "credit": history.credit
        }
        await ws_manager.send_generate_request(client_id, generate_request)
        print(f"📤 Generate isteği WebSocket'e gönderildi: {client_id}")
    else:
        # WebSocket bağlantısı yoksa simülasyon çalıştır
        print("⚠️  WebSocket bağlantısı yok, simülasyon başlatılıyor")
        asyncio.create_task(simulate_image_generation_simple(history.id, db))

    return GenerateStartResponse(
        history_id=history.id,
        message="Generate işlemi başlatıldı",
        status="processing"
    )

# --- GALLERY SERVISI ---
from pydantic import BaseModel

class UserGalleryItem(BaseModel):
    history_id: int
    generated_image_path: str
    generated_file_name: str
    generated_file_size: int
    created_at: datetime
    completed_at: datetime | None
    credit: int
    model_name: str
    status: str

@router.get("/gallery/{udid}", response_model=List[UserGalleryItem], tags=["Generate"])
async def get_user_gallery(
    udid: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Kullanıcının generate ettiği resimlerin ve detaylarının listesi
    """
    query = select(CreateImageHistory, GenerateModelItem).join(
        GenerateModelItem, CreateImageHistory.model_id == GenerateModelItem.id
    ).where(
        CreateImageHistory.udid == udid,
        CreateImageHistory.status == 'success'
    )
    result = await db.execute(query)
    items = []
    for history, model in result.fetchall():
        items.append(UserGalleryItem(
            history_id=history.id,
            generated_image_path=history.generated_image_path,
            generated_file_name=history.generated_file_name,
            generated_file_size=history.generated_file_size or 0,
            created_at=history.created_at,
            completed_at=history.completed_at,
            credit=history.credit,
            model_name=model.name,
            status=history.status
        ))
    return items