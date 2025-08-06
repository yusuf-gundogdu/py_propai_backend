from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
import os
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from typing import Dict

router = APIRouter(prefix="/userupload", tags=["UserUpload"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_user_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Kullanıcının yüklediği resmi user_uploads klasörüne kaydet"""
    
    # Klasörü oluştur (yoksa)
    save_dir = "user_uploads"
    os.makedirs(save_dir, exist_ok=True)

    # Dosya uzantısını al
    ext = os.path.splitext(file.filename)[1]
    
    # Unique dosya adı oluştur
    unique_id = str(uuid4())
    file_name = f"user_{unique_id}{ext}"
    file_path = os.path.join(save_dir, file_name)

    # Dosyayı kaydet
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return {
        "fileName": file_name,
        "filePath": file_path,
        "fileSize": len(content)
    }

@router.get("/{filename}")
async def get_user_image(filename: str):
    """Kullanıcının yüklediği resmi getir"""
    
    # Her zaman tam path ile eriş
    file_path = os.path.abspath(os.path.join("user_uploads", filename))
    print(f"[USERUPLOAD] İstek: {filename}")
    print(f"[USERUPLOAD] Dosya path: {file_path}")
    if not os.path.exists(file_path):
        print(f"[USERUPLOAD] Dosya bulunamadı: {file_path}")
        raise HTTPException(status_code=404, detail="Image file not found")
    try:
        from fastapi.responses import FileResponse
        print(f"[USERUPLOAD] Dosya bulundu, FileResponse ile döndürülüyor.")
        return FileResponse(file_path)
    except Exception as e:
        print(f"[USERUPLOAD] FileResponse hatası: {e}")
        raise HTTPException(status_code=500, detail=f"FileResponse error: {e}")