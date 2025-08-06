from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
import os
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.generatemodelitemimage import GenerateModelItemImage
from app.schemas.generatemodelitemimage import GenerateModelItemImageCreate, GenerateModelItemImageRead
from typing import List, Optional
from fastapi.responses import FileResponse
from sqlalchemy import update

router = APIRouter(prefix="/generatemodelitemimages", tags=["GenerateModelItemImage"])

@router.get("/", response_model=List[GenerateModelItemImageRead])
async def list_images(
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, le=1000), 
    image_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    if image_id:
        # Belirli bir resmi getir
        obj = await db.get(GenerateModelItemImage, image_id)
        if not obj:
            raise HTTPException(status_code=404, detail="Image not found")
        return [obj]
    else:
        # Tüm resimleri listele
        query = select(GenerateModelItemImage)
        result = await db.execute(query.offset(skip).limit(limit))
        return result.scalars().all()

@router.get("/{image_id}")
async def get_image(image_id: int, db: AsyncSession = Depends(get_db)):
    obj = await db.get(GenerateModelItemImage, image_id)
    if not obj:
        raise HTTPException(status_code=404, detail="GenerateModelItemImage not found")
    
    # Resim dosyasının var olup olmadığını kontrol et
    if not os.path.exists(obj.filePath):
        raise HTTPException(status_code=404, detail="Image file not found")
    
    # Resmi döndür
    return FileResponse(obj.filePath)

@router.post("/", response_model=GenerateModelItemImageRead, status_code=status.HTTP_201_CREATED)
async def upload_image_no_model(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    save_dir = "generate_model_image"
    os.makedirs(save_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1]
    unique_id = str(uuid4())
    file_name = f"{unique_id}{ext}"
    file_path = os.path.join(save_dir, file_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    obj = GenerateModelItemImage(
        fileName=file_name,
        filePath=file_path,
        fileSize=len(content)
    )
    db.add(obj)
    await db.commit()
    await db.refresh(obj)

    return obj

@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(image_id: int, db: AsyncSession = Depends(get_db)):
    obj = await db.get(GenerateModelItemImage, image_id)
    if not obj:
        raise HTTPException(status_code=404, detail="GenerateModelItemImage not found")
    
    # Önce bu görseli kullanan tüm model item'larda image_id'yi NULL yap
    await db.execute(
        update(__import__('app.models.generatemodelitem').models.generatemodelitem.GenerateModelItem)
        .where(__import__('app.models.generatemodelitem').models.generatemodelitem.GenerateModelItem.image_id == image_id)
        .values(image_id=None)
    )
    await db.commit()
    
    # Sonra dosyayı sil
    try:
        if os.path.exists(obj.filePath):
            os.remove(obj.filePath)
    except OSError as e:
        # Dosya silme hatası olsa bile veritabanı kaydını silmeye devam et
        print(f"Dosya silme hatası: {e}")
    
    # Veritabanı kaydını sil
    await db.delete(obj)
    await db.commit() 