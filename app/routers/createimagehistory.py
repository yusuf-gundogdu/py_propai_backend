from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.database import get_db
from app.models.createimagehistory import CreateImageHistory
from app.models.account import Account
from app.models.generatemodelitem import GenerateModelItem
from app.models.generatemodelitemimage import GenerateModelItemImage
from app.schemas.createimagehistory import CreateImageHistoryCreate, CreateImageHistoryRead, CreateImageHistoryUpdate
from typing import List, Optional
from datetime import datetime
import os
from uuid import uuid4

router = APIRouter(prefix="/createimagehistory", tags=["CreateImageHistory"])

@router.get("/", response_model=List[CreateImageHistoryRead])
async def list_create_image_histories(
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, le=1000), 
    udid: Optional[str] = None,
    model_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Tüm resim oluşturma geçmişini listele"""
    query = select(CreateImageHistory).options(
        joinedload(CreateImageHistory.model).joinedload(GenerateModelItem.image)
    )
    
    if udid:
        query = query.where(CreateImageHistory.udid == udid)
    if model_id:
        query = query.where(CreateImageHistory.model_id == model_id)
    if status_filter:
        query = query.where(CreateImageHistory.status == status_filter)
    
    query = query.order_by(CreateImageHistory.created_at.desc())
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{history_id}", response_model=CreateImageHistoryRead)
async def get_create_image_history(
    history_id: int, 
    db: AsyncSession = Depends(get_db)
):
    """Belirli bir resim oluşturma geçmişini getir"""
    query = select(CreateImageHistory).options(
        joinedload(CreateImageHistory.model).joinedload(GenerateModelItem.image)
    ).where(CreateImageHistory.id == history_id)
    
    result = await db.execute(query)
    history = result.scalar_one_or_none()
    
    if not history:
        raise HTTPException(status_code=404, detail="CreateImageHistory not found")
    
    return history



@router.get("/udid/{udid}", response_model=List[CreateImageHistoryRead])
async def get_udid_history(
    udid: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Belirli bir UDID'nin resim oluşturma geçmişini getir"""
    query = select(CreateImageHistory).options(
        joinedload(CreateImageHistory.model).joinedload(GenerateModelItem.image)
    ).where(CreateImageHistory.udid == udid)
    
    query = query.order_by(CreateImageHistory.created_at.desc())
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

@router.post("/", response_model=CreateImageHistoryRead, status_code=status.HTTP_201_CREATED)
async def create_image_history(
    data: CreateImageHistoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """Yeni resim oluşturma işlemi başlat"""
    
    # Model kontrolü
    model = await db.get(GenerateModelItem, data.model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # UDID'den hesabı bul - hesap olmalı (platform bilgisi olmadan)
    account_query = select(Account).where(Account.udid == data.udid)
    account_result = await db.execute(account_query)
    accounts = account_result.scalars().all()
    
    if not accounts:
        raise HTTPException(status_code=404, detail="Account not found with this UDID")
    
    # İlk hesabı al (eğer birden fazla varsa)
    account = accounts[0]
    
    # Model'den kredi ve seviye bilgilerini al
    model_credit = model.credit
    model_level = model.level
    
    print(f"DEBUG: Model ID {data.model_id} - Credit: {model_credit}, Level: {model_level}")
    print(f"DEBUG: Account UDID {data.udid} - Credit: {account.credit}, Level: {account.level}")
    
    # Kredi kontrolü - model'in kredisine göre
    if account.credit < model_credit:
        raise HTTPException(status_code=400, detail=f"Yetersiz kredi. Gerekli: {model_credit}, Mevcut: {account.credit}")
    
    # Seviye kontrolü - model'in seviyesine göre
    if account.level < model_level:
        raise HTTPException(status_code=400, detail=f"Üyeliğiniz bu generate modelini desteklemiyor. Gerekli seviye: {model_level}, Mevcut seviyeniz: {account.level}")
    
    # Yeni kayıt oluştur - model'den alınan kredi ve seviye ile
    history_data = data.model_dump()
    history_data['credit'] = model_credit  # Model'den alınan kredi
    history_data['level'] = account.level  # Kullanıcının seviyesi
    
    history = CreateImageHistory(**history_data)
    db.add(history)
    
    # Hesap kredisini güncelle - model'in kredisini düş (ipotekle)
    account.credit -= model_credit
    
    await db.commit()
    await db.refresh(history)
    
    # İlişkileri yükle
    query = select(CreateImageHistory).options(
        joinedload(CreateImageHistory.model).joinedload(GenerateModelItem.image)
    ).where(CreateImageHistory.id == history.id)
    
    result = await db.execute(query)
    return result.scalar_one()

@router.put("/{history_id}", response_model=CreateImageHistoryRead)
async def update_image_history(
    history_id: int,
    data: CreateImageHistoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Resim oluşturma işlemini güncelle (AI işlemi tamamlandığında)"""
    
    history = await db.get(CreateImageHistory, history_id)
    if not history:
        raise HTTPException(status_code=404, detail="CreateImageHistory not found")
    
    # Güncelleme verilerini al
    update_data = data.model_dump(exclude_unset=True)
    
    # Eğer işlem tamamlanıyorsa completed_at'i ayarla
    if update_data.get('status') in ['success', 'failed', 'cancelled'] and not history.completed_at:
        update_data['completed_at'] = datetime.utcnow()
    
    # Eğer işlem başlıyorsa started_at'i ayarla
    if update_data.get('status') == 'processing' and not history.started_at:
        update_data['started_at'] = datetime.utcnow()
    
    # Alanları güncelle
    for key, value in update_data.items():
        setattr(history, key, value)
    
    await db.commit()
    await db.refresh(history)
    
    # İlişkileri yükle
    query = select(CreateImageHistory).options(
        joinedload(CreateImageHistory.model).joinedload(GenerateModelItem.image)
    ).where(CreateImageHistory.id == history.id)
    
    result = await db.execute(query)
    return result.scalar_one()

@router.delete("/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image_history(
    history_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Resim oluşturma geçmişini sil"""
    
    history = await db.get(CreateImageHistory, history_id)
    if not history:
        raise HTTPException(status_code=404, detail="CreateImageHistory not found")
    
    # Dosyaları sil
    try:
        # Original image dosyasını sil
        if history.original_image_path and os.path.exists(history.original_image_path):
            os.remove(history.original_image_path)
            print(f"✅ Original image silindi: {history.original_image_path}")
        
        # Generated image dosyasını sil
        if history.generated_image_path:
            # Yeni sistem: images/generate_image/{dosya}
            if history.generated_image_path.startswith('images/generate_image/'):
                filename = history.generated_image_path.replace('images/generate_image/', '')
                generated_file_path = os.path.join('generate_image', filename)
                if os.path.exists(generated_file_path):
                    os.remove(generated_file_path)
                    print(f"✅ Generated image silindi: {generated_file_path}")
                else:
                    print(f"⚠️ Generated image dosyası bulunamadı: {generated_file_path}")
            elif history.generated_image_path.startswith('/api/aigenerated/'):
                filename = history.generated_image_path.replace('/api/aigenerated/', '')
                # ai_generated klasörü kaldırıldı, bu satır silindi
                if os.path.exists(generated_file_path):
                    os.remove(generated_file_path)
                    print(f"✅ Generated image silindi: {generated_file_path}")
                else:
                    print(f"⚠️ Generated image dosyası bulunamadı: {generated_file_path}")
            elif history.generated_image_path.startswith('/api/generatemodelitemimages/'):
                filename = history.generated_image_path.replace('/api/generatemodelitemimages/', '')
                generated_file_path = os.path.join('generate_image', filename)
                if os.path.exists(generated_file_path):
                    os.remove(generated_file_path)
                    print(f"✅ Generated image silindi: {generated_file_path}")
                else:
                    print(f"⚠️ Generated image dosyası bulunamadı: {generated_file_path}")
            else:
                print(f"⚠️ Bilinmeyen generated_image_path formatı: {history.generated_image_path}")
    except Exception as e:
        print(f"⚠️ Dosya silme hatası: {e}")
    
    # Database kaydını sil
    await db.delete(history)
    await db.commit()
    
    print(f"✅ History {history_id} ve ilgili dosyalar silindi") 