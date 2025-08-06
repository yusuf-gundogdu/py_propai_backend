from fastapi import APIRouter
router = APIRouter(prefix="/generate", tags=["Generate"])

# --- YENİ: /api/upload-generated-image endpointi (ws_client için) ---
from fastapi import UploadFile, File, Form
import json as pyjson

@router.post("/upload-generated-image")
async def upload_generated_image(
    json: str = Form(...),
    file: UploadFile = File(...)
):
    """
    ws_client tarafından ComfyUI generate işlemi sonrası çağrılır.
    - 'json': {action, generate_id, udid} içeren string
    - 'file': Görsel dosyası (ör. PNG)
    """
    try:
        data = pyjson.loads(json)
    except Exception as e:
        return {"success": False, "error": f"JSON parse hatası: {e}"}

    generate_id = data.get("generate_id")
    udid = data.get("udid")
    action = data.get("action")
    if not (generate_id and udid and action == "generated_image"):
        return {"success": False, "error": "Eksik veya hatalı alanlar"}

    # Dosya kaydet
    ext = ".png"
    if file.filename and "." in file.filename:
        ext = "." + file.filename.split(".")[-1]
    filename = f"generated_{generate_id}{ext}"
    save_path = f"generate_image/{filename}"
    try:
        with open(save_path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        return {"success": False, "error": f"Dosya kaydedilemedi: {e}"}

    # Gerekirse burada veritabanına kayıt veya başka işlem yapılabilir

    # Dışarıdan erişilebilecek URL üret
    from os import getenv
    server_url = getenv("SERVER_URL", "https://propai.store")
    image_url = f"{server_url}/api/generateimage/{filename}"

    return {
        "success": True,
        "generate_id": generate_id,
        "udid": udid,
        "image_url": image_url
    }
# --- YENİ: /api/upload-generated-image endpointi (ws_client için) ---
from fastapi import UploadFile, File, Form
import json as pyjson

# --- YENİ: /api/upload-generated-image endpointi (ws_client için) ---
from fastapi import UploadFile, File, Form
import json as pyjson

# ...existing code...

# Bu endpoint router tanımından sonra olmalı!
@router.post("/upload-generated-image")
async def upload_generated_image(
    json: str = Form(...),
    file: UploadFile = File(...)
):
    """
    ws_client tarafından ComfyUI generate işlemi sonrası çağrılır.
    - 'json': {action, generate_id, udid} içeren string
    - 'file': Görsel dosyası (ör. PNG)
    """
    try:
        data = pyjson.loads(json)
    except Exception as e:
        return {"success": False, "error": f"JSON parse hatası: {e}"}

    generate_id = data.get("generate_id")
    udid = data.get("udid")
    action = data.get("action")
    if not (generate_id and udid and action == "generated_image"):
        return {"success": False, "error": "Eksik veya hatalı alanlar"}

    # Dosya kaydet
    ext = ".png"
    if file.filename and "." in file.filename:
        ext = "." + file.filename.split(".")[-1]
    filename = f"generated_{generate_id}{ext}"
    save_path = f"generate_image/{filename}"
    try:
        with open(save_path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        return {"success": False, "error": f"Dosya kaydedilemedi: {e}"}

    # Gerekirse burada veritabanına kayıt veya başka işlem yapılabilir

    # Dışarıdan erişilebilecek URL üret
    from os import getenv
    server_url = getenv("SERVER_URL", "https://propai.store")
    image_url = f"{server_url}/api/generateimage/{filename}"

    return {
        "success": True,
        "generate_id": generate_id,
        "udid": udid,
        "image_url": image_url
    }

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
from datetime import timezone


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
    
    await asyncio.sleep(10)

    from app.database import engine
    async with engine.begin() as conn:
        query = select(CreateImageHistory).where(CreateImageHistory.id == history_id)
        result = await conn.execute(query)
        history = result.scalar_one_or_none()

        if not history:
            print(f"History {history_id} bulunamadı")
            return

        generated_filename = f"ai_{uuid4()}.jpg"
        test_image_path = os.path.join("generate_image", generated_filename)
        file_size = 0
        try:
            user_uploads_dir = "user_uploads"
            if os.path.exists(user_uploads_dir):
                user_images = [f for f in os.listdir(user_uploads_dir) if f.endswith((".jpg", ".jpeg", ".png"))]
                if user_images:
                    random_image = random.choice(user_images)
                    source_path = os.path.join(user_uploads_dir, random_image)
                    shutil.copy2(source_path, test_image_path)
                    file_size = os.path.getsize(test_image_path)
                    print(f"✅ AI resmi oluşturuldu: {test_image_path} (Kaynak: {random_image}, Boyut: {file_size} bytes)")
                else:
                    with open(test_image_path, "wb") as f:
                        test_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00d\x00d\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
                        f.write(test_image_data)
                        file_size = len(test_image_data)
                    print(f"✅ AI resmi oluşturuldu: {test_image_path} (Placeholder, Boyut: {file_size} bytes)")
            else:
                with open(test_image_path, "wb") as f:
                    test_image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00d\x00d\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
                    f.write(test_image_data)
                    file_size = len(test_image_data)
                print(f"✅ AI resmi oluşturuldu: {test_image_path} (Placeholder, Boyut: {file_size} bytes)")

            update_data = {
                'status': 'completed',
                'generated_image_path': test_image_path,
                'generated_file_name': generated_filename,
                'generated_file_size': file_size,
                'completed_at': datetime.utcnow(),
                'processing_time_seconds': 10,
                'error_message': None
            }
        except Exception as e:
            print(f"❌ AI resmi oluşturulurken hata: {e}")
            update_data = {
                'status': 'failed',
                'generated_image_path': None,
                'generated_file_name': None,
                'generated_file_size': None,
                'completed_at': datetime.utcnow(),
                'processing_time_seconds': 10,
                'error_message': f'AI resmi oluşturulurken hata: {e}'
            }
            account_query = select(Account).where(Account.udid == history.udid)
            account_result = await conn.execute(account_query)
            account = account_result.scalar_one_or_none()
            if account:
                account.credit += history.credit
                print(f"❌ İşlem {history_id} başarısız oldu, {history.credit} kredi geri verildi")
            else:
                print(f"❌ İşlem {history_id} başarısız oldu, hesap bulunamadı")

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
        
    # Bu fonksiyonun ai_generated klasörüyle ilgili kodları kaldırıldı.
    print("[simulate_image_generation_simple] ai_generated klasörü ve ilgili kodlar kaldırıldı.")

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



# YENİ: /upload/{model_id} endpointi
@router.post("/upload/{model_id}", response_model=GenerateStartResponse)
async def upload_image(
    model_id: int,
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    print("[DEBUG] upload_image fonksiyonu çalıştı. model_id:", model_id)
    """
    Kullanıcı model_id ve image gönderir. generate_id backend'de otomatik oluşturulur.
    UDID, image ve model_id ile yeni bir history kaydı oluşturulur.
    """
    # Kullanıcıyı (udid) image ile birlikte formdan veya header'dan al
    # (örnek: udid form-data ile gönderilebilir veya authentication'dan alınabilir)
    # Burada örnek olarak udid'i dosya adından alıyoruz: udid__filename.jpg
    udid = None
    try:
        udid = image.filename.split("__")[0]  # örnek: udid__filename.jpg
    except Exception:
        pass
    if not udid:
        raise HTTPException(status_code=400, detail="UDID alınamadı. Lütfen dosya adını udid__filename.jpg formatında gönderin.")

    # Modeli bul
    model_query = select(GenerateModelItem).where(GenerateModelItem.id == model_id)
    model_result = await db.execute(model_query)
    model = model_result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model bulunamadı.")

    # Kullanıcı hesabını bul
    account_query = select(Account).where(Account.udid == udid)
    account_result = await db.execute(account_query)
    account = account_result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Kullanıcı hesabı bulunamadı.")

    # Kredi ve level kontrolü
    if account.credit < model.credit:
        raise HTTPException(status_code=400, detail=f"Yetersiz kredi. Model için {model.credit} kredi gerekli, hesabınızda {account.credit} kredi var.")
    if account.level < model.level:
        raise HTTPException(status_code=403, detail=f"Bu model için Level {model.level} gerekli. Şu anda Level {account.level} kullanıcısısınız.")

    # generate_id oluştur
    generate_id = str(uuid4())

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
        if account and model and account.credit >= model.credit:
            account.credit -= model.credit
            await db.commit()
            await db.refresh(account)
            print(f"✅ Kullanıcı {account.udid} için {model.credit} kredi düşüldü. Yeni kredi: {account.credit}")
        else:
            print(f"❌ Kredi düşümü başarısız: model veya kredi yetersiz.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resim kaydedilirken hata oluştu: {str(e)}")

    # Yeni history kaydı oluştur
    history = CreateImageHistory(
        udid=udid,
        model_id=model_id,
        generate_id=generate_id,
        original_image_path=f"/api/userupload/{unique_filename}",
        original_file_size=file_size,
        original_file_name=image.filename,
        credit=model.credit,
        level=account.level,
        status='processing',
        started_at=datetime.utcnow()
    )
    db.add(history)
    await db.commit()
    await db.refresh(history)

    # --- WS JSON MESAJI GÖNDER ---

    import json
    import requests

    # Dışarıdan erişilebilen bir URL kullan
    # .env dosyasına SERVER_URL eklenmişse onu kullan, yoksa fallback olarak propai.store
    server_url = os.getenv("SERVER_URL", "https://propai.store")
    image_url = f"{server_url}{history.original_image_path}" if history.original_image_path else None

    ws_payload = {
        "action": "generate_image",
        "generate_id": history.generate_id,
        "udid": history.udid,
        "model_id": str(history.model_id),
        "ksampler": {
            "sampler_name": model.sampler_name if model else None,
            "cfg": model.cfg if model else None,
            "steps": model.steps if model else None,
            "model": model.model if model else None,
            "positive_prompt": model.positive_prompt if model else None,
            "negative_prompt": model.negative_prompt if model else None,
            "seed": model.seed if model else None,
            "denoise": model.denoise if model else None,
            "scheduler": model.scheduler if model else None
        },
        "image_url": image_url,
        "timestamp": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    }

    # Broadcast API'ye POST ile gönder
    try:
        print("[WS] Broadcast API'ye gönderilecek JSON:")
        print(json.dumps(ws_payload, ensure_ascii=False, indent=2))
        resp = requests.post("http://127.0.0.1:8876", json=ws_payload, timeout=2)
        print(f"[WS] Broadcast API yanıtı: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"[WS] Broadcast API'ye mesaj gönderilemedi: {e}")

    return GenerateStartResponse(
        history_id=history.id,
        message="WS mesajı gönderildi",
        status="processing",
        generate_id=history.generate_id,
        udid=history.udid,
        model_id=history.model_id,
        ksampler=ws_payload["ksampler"],
        image_url=image_url,
        timestamp=ws_payload["timestamp"]
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