from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
import os
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from typing import Dict

router = APIRouter(prefix="/aigenerated", tags=["AIGenerated"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def save_ai_generated_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """AI'ın generate ettiği resmi ai_generated klasörüne kaydet"""
    
    # Klasörü oluştur (yoksa)
    save_dir = "ai_generated"
    os.makedirs(save_dir, exist_ok=True)

    # Dosya uzantısını al
    ext = os.path.splitext(file.filename)[1]
    
    # Unique dosya adı oluştur
    unique_id = str(uuid4())
    file_name = f"ai_{unique_id}{ext}"
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
async def get_ai_generated_image(filename: str):
    """AI'ın generate ettiği resmi getir"""
    
    file_path = os.path.join("ai_generated", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Generated image file not found")
    
    from fastapi.responses import FileResponse
    return FileResponse(file_path) 